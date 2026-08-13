import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader

from torchvision import datasets
from torchvision import transforms

from PIL import Image


# ============================================================
# 1. 기본 설정
# ============================================================

TRAIN_DIR = "./dataset/train"
VAL_DIR = "./dataset/val"

MODEL_SAVE_PATH = "./resnet18_best.pth"

IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 0.001

NUM_WORKERS = 0

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print(f"DEVICE: {DEVICE}")


# ============================================================
# 2. BasicBlock
#
# ResNet-18 / ResNet-34에서 사용하는 Residual Block
#
# 입력 x
#   │
#   ├─────────────── shortcut ──────────────┐
#   │                                       │
# Conv3x3                                   │
# BatchNorm                                 │
# ReLU                                      │
# Conv3x3                                   │
# BatchNorm                                 │
#   │                                       │
#   └──────────── + ────────────────────────┘
#                   │
#                  ReLU
#
# ============================================================

class BasicBlock(nn.Module):

    # BasicBlock의 출력 채널 배율
    expansion = 1

    def __init__(
        self,
        in_channels,
        out_channels,
        stride=1,
        downsample=None,
    ):
        super().__init__()

        # ----------------------------------------------------
        # 첫 번째 3x3 Convolution
        #
        # stride=2가 들어오면
        # feature map 크기를 절반으로 감소시킨다.
        # ----------------------------------------------------
        self.conv1 = nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
            bias=False,
        )

        self.bn1 = nn.BatchNorm2d(
            out_channels
        )

        self.relu = nn.ReLU(
            inplace=True
        )

        # ----------------------------------------------------
        # 두 번째 3x3 Convolution
        # ----------------------------------------------------
        self.conv2 = nn.Conv2d(
            in_channels=out_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False,
        )

        self.bn2 = nn.BatchNorm2d(
            out_channels
        )

        # ----------------------------------------------------
        # 입력 x의 크기와
        # convolution 결과의 크기가 다를 경우
        # shortcut 크기를 맞추는 용도
        # ----------------------------------------------------
        self.downsample = downsample

    def forward(self, x):

        # shortcut에 사용할 원본 입력
        identity = x

        # -----------------------------
        # 첫 번째 Conv
        # -----------------------------
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        # -----------------------------
        # 두 번째 Conv
        # -----------------------------
        out = self.conv2(out)
        out = self.bn2(out)

        # -----------------------------
        # 크기가 다른 경우
        # shortcut도 변환
        # -----------------------------
        if self.downsample is not None:
            identity = self.downsample(x)

        # -----------------------------
        # 핵심: Residual Connection
        #
        # F(x) + x
        # -----------------------------
        out = out + identity

        out = self.relu(out)

        return out


# ============================================================
# 3. ResNet 모델
# ============================================================

class ResNet(nn.Module):

    def __init__(
        self,
        block,
        layers,
        num_classes,
    ):
        super().__init__()

        # 현재 feature map의 channel 수
        self.in_channels = 64

        # ====================================================
        # 입력 부분
        #
        # 224 x 224
        # ↓
        # Conv7x7 stride=2
        # ↓
        # 112 x 112
        # ↓
        # MaxPool stride=2
        # ↓
        # 56 x 56
        # ====================================================

        self.conv1 = nn.Conv2d(
            in_channels=3,
            out_channels=64,
            kernel_size=7,
            stride=2,
            padding=3,
            bias=False,
        )

        self.bn1 = nn.BatchNorm2d(
            64
        )

        self.relu = nn.ReLU(
            inplace=True
        )

        self.maxpool = nn.MaxPool2d(
            kernel_size=3,
            stride=2,
            padding=1,
        )

        # ====================================================
        # ResNet Layer
        #
        # ResNet-18:
        #
        # layer1 : 64  channels, 2 blocks
        # layer2 : 128 channels, 2 blocks
        # layer3 : 256 channels, 2 blocks
        # layer4 : 512 channels, 2 blocks
        # ====================================================

        self.layer1 = self._make_layer(
            block=block,
            out_channels=64,
            blocks=layers[0],
            stride=1,
        )

        self.layer2 = self._make_layer(
            block=block,
            out_channels=128,
            blocks=layers[1],
            stride=2,
        )

        self.layer3 = self._make_layer(
            block=block,
            out_channels=256,
            blocks=layers[2],
            stride=2,
        )

        self.layer4 = self._make_layer(
            block=block,
            out_channels=512,
            blocks=layers[3],
            stride=2,
        )

        # ====================================================
        # Global Average Pooling
        #
        # H x W 크기를 1 x 1로 변환
        # ====================================================

        self.avgpool = nn.AdaptiveAvgPool2d(
            output_size=(1, 1)
        )

        # ====================================================
        # 최종 Classification Layer
        # ====================================================

        self.fc = nn.Linear(
            512 * block.expansion,
            num_classes,
        )

        # weight 초기화
        self._initialize_weights()

    # ========================================================
    # Residual Layer 생성 함수
    # ========================================================

    def _make_layer(
        self,
        block,
        out_channels,
        blocks,
        stride,
    ):

        downsample = None

        # ----------------------------------------------------
        # 입력/출력 channel이 다르거나
        # stride가 1이 아닌 경우
        #
        # shortcut의 크기를 맞춰줘야 한다.
        # ----------------------------------------------------

        if (
            stride != 1
            or self.in_channels
            != out_channels * block.expansion
        ):
            downsample = nn.Sequential(

                nn.Conv2d(
                    in_channels=self.in_channels,
                    out_channels=(
                        out_channels
                        * block.expansion
                    ),
                    kernel_size=1,
                    stride=stride,
                    bias=False,
                ),

                nn.BatchNorm2d(
                    out_channels
                    * block.expansion
                ),
            )

        layers = []

        # ----------------------------------------------------
        # 첫 번째 block
        #
        # feature map 크기 또는 channel 수가
        # 변경될 수 있다.
        # ----------------------------------------------------

        layers.append(

            block(
                in_channels=self.in_channels,
                out_channels=out_channels,
                stride=stride,
                downsample=downsample,
            )

        )

        # 현재 channel 업데이트
        self.in_channels = (
            out_channels
            * block.expansion
        )

        # ----------------------------------------------------
        # 나머지 block
        # ----------------------------------------------------

        for _ in range(
            1,
            blocks
        ):

            layers.append(

                block(
                    in_channels=self.in_channels,
                    out_channels=out_channels,
                    stride=1,
                    downsample=None,
                )

            )

        return nn.Sequential(
            *layers
        )

    # ========================================================
    # Weight 초기화
    # ========================================================

    def _initialize_weights(self):

        for module in self.modules():

            if isinstance(
                module,
                nn.Conv2d
            ):

                nn.init.kaiming_normal_(
                    module.weight,
                    mode="fan_out",
                    nonlinearity="relu",
                )

            elif isinstance(
                module,
                nn.BatchNorm2d
            ):

                nn.init.constant_(
                    module.weight,
                    1
                )

                nn.init.constant_(
                    module.bias,
                    0
                )

            elif isinstance(
                module,
                nn.Linear
            ):

                nn.init.normal_(
                    module.weight,
                    0,
                    0.01
                )

                nn.init.constant_(
                    module.bias,
                    0
                )

    # ========================================================
    # Forward
    # ========================================================

    def forward(self, x):

        # 입력
        # [B, 3, 224, 224]

        x = self.conv1(x)

        # [B, 64, 112, 112]

        x = self.bn1(x)
        x = self.relu(x)

        x = self.maxpool(x)

        # [B, 64, 56, 56]

        x = self.layer1(x)

        # [B, 64, 56, 56]

        x = self.layer2(x)

        # [B, 128, 28, 28]

        x = self.layer3(x)

        # [B, 256, 14, 14]

        x = self.layer4(x)

        # [B, 512, 7, 7]

        x = self.avgpool(x)

        # [B, 512, 1, 1]

        x = torch.flatten(
            x,
            start_dim=1
        )

        # [B, 512]

        x = self.fc(x)

        # [B, num_classes]

        return x


# ============================================================
# 4. ResNet-18 생성 함수
# ============================================================

def resnet18(
    num_classes
):

    return ResNet(
        block=BasicBlock,

        # ResNet-18
        # 각 Layer가 가지는 BasicBlock 수
        layers=[
            2,
            2,
            2,
            2,
        ],

        num_classes=num_classes,
    )


# ============================================================
# 5. 이미지 전처리
# ============================================================

train_transform = transforms.Compose(
    [

        transforms.Resize(
            (IMAGE_SIZE, IMAGE_SIZE)
        ),

        # 학습 데이터 augmentation
        transforms.RandomHorizontalFlip(),

        transforms.RandomRotation(
            degrees=10
        ),

        transforms.ToTensor(),

        # ImageNet 평균/표준편차
        transforms.Normalize(
            mean=[
                0.485,
                0.456,
                0.406,
            ],
            std=[
                0.229,
                0.224,
                0.225,
            ],
        ),
    ]
)


val_transform = transforms.Compose(
    [

        transforms.Resize(
            (IMAGE_SIZE, IMAGE_SIZE)
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[
                0.485,
                0.456,
                0.406,
            ],
            std=[
                0.229,
                0.224,
                0.225,
            ],
        ),
    ]
)


# ============================================================
# 6. Dataset / DataLoader
# ============================================================

train_dataset = datasets.ImageFolder(
    root=TRAIN_DIR,
    transform=train_transform,
)

val_dataset = datasets.ImageFolder(
    root=VAL_DIR,
    transform=val_transform,
)


print()
print("===================================")
print("Dataset Information")
print("===================================")

print(
    "Train images:",
    len(train_dataset)
)

print(
    "Validation images:",
    len(val_dataset)
)

print(
    "Classes:",
    train_dataset.classes
)

print(
    "Class to index:",
    train_dataset.class_to_idx
)

print()


train_loader = DataLoader(
    dataset=train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
)

val_loader = DataLoader(
    dataset=val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
)


# ============================================================
# 7. 모델 생성
# ============================================================

NUM_CLASSES = len(
    train_dataset.classes
)

model = resnet18(
    num_classes=NUM_CLASSES
)

model = model.to(
    DEVICE
)


print(
    model
)


# ============================================================
# 8. Loss Function
# ============================================================

criterion = nn.CrossEntropyLoss()


# ============================================================
# 9. Optimizer
# ============================================================

optimizer = optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)


# ============================================================
# 10. 한 Epoch 학습
# ============================================================

def train_one_epoch(
    model,
    data_loader,
    criterion,
    optimizer,
    device,
):

    # 학습 모드
    model.train()

    running_loss = 0.0

    correct = 0
    total = 0

    for images, labels in data_loader:

        images = images.to(
            device
        )

        labels = labels.to(
            device
        )

        # ----------------------------------------------------
        # 이전 gradient 초기화
        # ----------------------------------------------------

        optimizer.zero_grad()

        # ----------------------------------------------------
        # Forward
        # ----------------------------------------------------

        outputs = model(
            images
        )

        # ----------------------------------------------------
        # Loss
        # ----------------------------------------------------

        loss = criterion(
            outputs,
            labels
        )

        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        loss.backward()

        # ----------------------------------------------------
        # Weight Update
        # ----------------------------------------------------

        optimizer.step()

        # ----------------------------------------------------
        # Loss 누적
        # ----------------------------------------------------

        running_loss += (
            loss.item()
            * images.size(0)
        )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        predictions = outputs.argmax(
            dim=1
        )

        correct += (
            predictions
            == labels
        ).sum().item()

        total += labels.size(0)

    epoch_loss = (
        running_loss
        / total
    )

    epoch_accuracy = (
        correct
        / total
    )

    return (
        epoch_loss,
        epoch_accuracy,
    )


# ============================================================
# 11. Validation
# ============================================================

def validate(
    model,
    data_loader,
    criterion,
    device,
):

    # 평가 모드
    model.eval()

    running_loss = 0.0

    correct = 0
    total = 0

    # gradient 계산하지 않음
    with torch.no_grad():

        for images, labels in data_loader:

            images = images.to(
                device
            )

            labels = labels.to(
                device
            )

            # Forward
            outputs = model(
                images
            )

            # Loss
            loss = criterion(
                outputs,
                labels
            )

            running_loss += (
                loss.item()
                * images.size(0)
            )

            predictions = outputs.argmax(
                dim=1
            )

            correct += (
                predictions
                == labels
            ).sum().item()

            total += labels.size(0)

    epoch_loss = (
        running_loss
        / total
    )

    epoch_accuracy = (
        correct
        / total
    )

    return (
        epoch_loss,
        epoch_accuracy,
    )


# ============================================================
# 12. 학습
# ============================================================

best_val_accuracy = 0.0


print()
print("===================================")
print("Training Start")
print("===================================")


for epoch in range(
    EPOCHS
):

    train_loss, train_accuracy = (
        train_one_epoch(
            model=model,
            data_loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=DEVICE,
        )
    )

    val_loss, val_accuracy = validate(
        model=model,
        data_loader=val_loader,
        criterion=criterion,
        device=DEVICE,
    )

    print(
        f"[{epoch + 1:02d}/{EPOCHS:02d}] "
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_accuracy * 100:.2f}% | "
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_accuracy * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Validation 정확도가 가장 높은 모델 저장
    # --------------------------------------------------------

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = (
            val_accuracy
        )

        torch.save(
            model.state_dict(),
            MODEL_SAVE_PATH,
        )

        print(
            "  -> Best model saved:",
            MODEL_SAVE_PATH
        )


print()
print("===================================")
print("Training Finished")
print("===================================")

print(
    f"Best Validation Accuracy: "
    f"{best_val_accuracy * 100:.2f}%"
)


# ============================================================
# 13. 저장된 모델 다시 불러오기
# ============================================================

model.load_state_dict(
    torch.load(
        MODEL_SAVE_PATH,
        map_location=DEVICE,
    )
)

model.eval()


# ============================================================
# 14. 단일 이미지 추론 함수
# ============================================================

def predict_image(
    image_path,
    model,
    class_names,
    device,
):

    image = Image.open(
        image_path
    ).convert(
        "RGB"
    )

    image_tensor = val_transform(
        image
    )

    # [C, H, W]
    # →
    # [1, C, H, W]

    image_tensor = (
        image_tensor
        .unsqueeze(0)
        .to(device)
    )

    with torch.no_grad():

        output = model(
            image_tensor
        )

        # softmax 확률 계산
        probabilities = torch.softmax(
            output,
            dim=1,
        )

        confidence, prediction = (
            probabilities.max(
                dim=1
            )
        )

    predicted_class = (
        class_names[
            prediction.item()
        ]
    )

    confidence = (
        confidence.item()
    )

    return (
        predicted_class,
        confidence,
    )


# ============================================================
# 15. 테스트 이미지가 있다면 추론
# ============================================================

TEST_IMAGE_PATH = "./test.jpg"


if os.path.exists(
    TEST_IMAGE_PATH
):

    predicted_class, confidence = (
        predict_image(
            image_path=TEST_IMAGE_PATH,
            model=model,
            class_names=train_dataset.classes,
            device=DEVICE,
        )
    )

    print()
    print(
        "==================================="
    )
    print(
        "Prediction Result"
    )
    print(
        "==================================="
    )

    print(
        "Prediction:",
        predicted_class
    )

    print(
        f"Confidence: "
        f"{confidence * 100:.2f}%"
    )