
import os
import random

import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import resnet18, ResNet18_Weights


# ------------------------------------------------------------
# 1. 랜덤 seed 고정
# ------------------------------------------------------------

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ------------------------------------------------------------
# 2. 실행 장치 설정
# ------------------------------------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=== 실행 장치 확인 ===")
print("device:", device)
print()


# ------------------------------------------------------------
# 3. CIFAR-10 클래스 이름 정의
# ------------------------------------------------------------

class_names = [
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
]

num_classes = len(class_names)

print("=== CIFAR-10 클래스 정보 ===")
print("num_classes:", num_classes)
print("class_names:", class_names)
print()


# ------------------------------------------------------------
# 4. pretrained ResNet18 불러오기
# ------------------------------------------------------------
# ResNet18_Weights.DEFAULT:
# - torchvision에서 제공하는 기본 pretrained weight를 사용한다.
# - 처음 실행할 때는 weight 파일을 다운로드할 수 있다.
#
# 주의:
# - 인터넷 연결이 필요할 수 있다.
# - 이미 다운로드되어 있으면 캐시에서 불러온다.
# ------------------------------------------------------------

weights = ResNet18_Weights.DEFAULT

pretrained_model = resnet18(
    weights=weights,
).to(device)

pretrained_model.eval()

print("=== Pretrained ResNet18 구조 확인 ===")
print(pretrained_model)
print()


# ------------------------------------------------------------
# 5. ResNet18의 마지막 fc layer 확인
# ------------------------------------------------------------
# ImageNet으로 학습된 ResNet18은 기본적으로 1000개 클래스를 출력한다.
#
# 따라서 마지막 fc layer는 보통 아래 형태이다.
#
# Linear(in_features=512, out_features=1000)
#
# CIFAR-10은 class가 10개이므로 out_features를 10으로 바꿔야 한다.
# ------------------------------------------------------------

print("=== ResNet18 마지막 fc layer 확인 ===")
print(pretrained_model.fc)
print()

print("fc 입력 feature 수:", pretrained_model.fc.in_features)
print("fc 출력 class 수  :", pretrained_model.fc.out_features)
print()


# ------------------------------------------------------------
# 6. 더미 입력으로 pretrained ResNet18 출력 확인
# ------------------------------------------------------------
# ImageNet pretrained model은 보통 224x224 RGB 이미지를 기준으로 사용한다.
#
# 입력:
# [N, 3, 224, 224]
#
# 출력:
# [N, 1000]
#
# 여기서 1000은 ImageNet class 수이다.
# ------------------------------------------------------------

dummy_input = torch.randn(
    4,
    3,
    224,
    224,
).to(device)

with torch.no_grad():
    dummy_logits = pretrained_model(dummy_input)

print("=== Pretrained ResNet18 더미 입력 출력 확인 ===")
print("dummy_input shape :", dummy_input.shape)
print("dummy_logits shape:", dummy_logits.shape)
print()


# ------------------------------------------------------------
# 7. CIFAR-10용 transform 준비
# ------------------------------------------------------------
# pretrained ResNet18은 ImageNet 이미지 전처리 기준에 맞춰 사용하는 것이 일반적이다.
#
# 여기서는 CIFAR-10의 32x32 이미지를 224x224로 키운다.
#
# 이유:
# - torchvision의 pretrained ResNet18은 ImageNet 스타일 입력을 기준으로 많이 사용된다.
# - 뒤쪽 전이학습 실습에서 입력을 통일하기 위함이다.
#
# Normalize:
# - ImageNet pretrained 모델에 자주 사용하는 mean/std를 적용한다.
# ------------------------------------------------------------

imagenet_mean = [0.485, 0.456, 0.406]
imagenet_std = [0.229, 0.224, 0.225]

train_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=imagenet_mean,
            std=imagenet_std,
        ),
    ]
)

test_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=imagenet_mean,
            std=imagenet_std,
        ),
    ]
)


# ------------------------------------------------------------
# 8. CIFAR-10 데이터셋 준비
# ------------------------------------------------------------
# 이번 실습에서는 학습하지 않는다.
# 전이학습 준비를 위해 batch shape만 확인한다.
# ------------------------------------------------------------

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

train_dataset = datasets.CIFAR10(
    root=DATA_DIR,
    train=True,
    transform=train_transform,
    download=True,
)

test_dataset = datasets.CIFAR10(
    root=DATA_DIR,
    train=False,
    transform=test_transform,
    download=True,
)

BATCH_SIZE = 8

train_loader = DataLoader(
    dataset=train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
)

test_loader = DataLoader(
    dataset=test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
)

images, labels = next(iter(train_loader))

print("=== 전이학습용 CIFAR-10 batch 확인 ===")
print("images shape:", images.shape)
print("labels shape:", labels.shape)
print()

print("해석:")
print("[8, 3, 224, 224] 형태로 ResNet18에 입력할 준비가 되었습니다.")
print()


# ------------------------------------------------------------
# 9. Normalize된 이미지 시각화용 복원 함수
# ------------------------------------------------------------
# Normalize를 적용한 이미지는 바로 plt.imshow로 보면 색이 이상할 수 있다.
# 그래서 시각화할 때는 Normalize를 되돌린다.
# ------------------------------------------------------------

def denormalize_image(image_tensor, mean, std):
    """
    Normalize된 이미지를 시각화 가능한 형태로 되돌린다.

    입력:
        image_tensor: [3, H, W]

    출력:
        [H, W, 3] numpy 배열
    """

    image = image_tensor.detach().cpu().clone()

    mean_tensor = torch.tensor(mean).view(3, 1, 1)
    std_tensor = torch.tensor(std).view(3, 1, 1)

    image = image * std_tensor + mean_tensor

    # 시각화 안전 범위로 자르기
    image = torch.clamp(image, 0, 1)

    image_for_plot = image.permute(1, 2, 0).numpy()

    return image_for_plot


def show_transfer_batch(images, labels, class_names, mean, std, rows=2, cols=4):
    """
    전이학습 transform이 적용된 이미지를 다시 복원해서 시각화한다.
    """

    plt.figure(figsize=(3 * cols, 3 * rows))

    for i in range(rows * cols):
        image_for_plot = denormalize_image(
            image_tensor=images[i],
            mean=mean,
            std=std,
        )

        label_id = labels[i].item()

        plt.subplot(rows, cols, i + 1)
        plt.imshow(image_for_plot)
        plt.title(class_names[label_id])
        plt.axis("off")

    plt.suptitle("CIFAR-10 Images for Transfer Learning")
    plt.tight_layout()
    plt.show()


show_transfer_batch(
    images=images,
    labels=labels,
    class_names=class_names,
    mean=imagenet_mean,
    std=imagenet_std,
    rows=2,
    cols=4,
)


# ------------------------------------------------------------
# 10. pretrained ResNet18에 CIFAR-10 batch 넣어보기
# ------------------------------------------------------------
# 아직 마지막 fc layer를 교체하지 않았기 때문에 출력은 1000개이다.
# ------------------------------------------------------------

images = images.to(device)
labels = labels.to(device)

pretrained_model.eval()

with torch.no_grad():
    imagenet_logits = pretrained_model(images)

print("=== CIFAR-10 batch를 pretrained ResNet18에 넣은 결과 ===")
print("입력 images shape       :", images.shape)
print("출력 imagenet_logits shape:", imagenet_logits.shape)
print()

print("해석:")
print("아직 마지막 fc layer가 ImageNet 1000개 class 기준이므로 출력은 [batch, 1000]입니다.")
print()


# ------------------------------------------------------------
# 11. CIFAR-10용 ResNet18 만들기
# ------------------------------------------------------------
# 이제 마지막 fc layer를 CIFAR-10 class 수에 맞게 교체한다.
#
# 기존:
# Linear(512 -> 1000)
#
# 변경:
# Linear(512 -> 10)
# ------------------------------------------------------------

transfer_model = resnet18(
    weights=weights,
).to(device)

in_features = transfer_model.fc.in_features

transfer_model.fc = nn.Linear(
    in_features=in_features,
    out_features=num_classes,
).to(device)

transfer_model.eval()

print("=== CIFAR-10용으로 fc layer 교체 완료 ===")
print("새로운 fc layer:", transfer_model.fc)
print()


# ------------------------------------------------------------
# 12. fc 교체 후 출력 shape 확인
# ------------------------------------------------------------

with torch.no_grad():
    cifar_logits = transfer_model(images)

print("=== fc 교체 후 출력 확인 ===")
print("입력 images shape :", images.shape)
print("출력 logits shape :", cifar_logits.shape)
print()

print("해석:")
print("이제 출력이 [batch, 10]입니다.")
print("즉, CIFAR-10 class 10개를 예측할 수 있는 구조가 되었습니다.")
print()


# ------------------------------------------------------------
# 13. logits와 softmax 확률 확인
# ------------------------------------------------------------
# 아직 fc layer는 새로 만든 랜덤 초기화 layer이므로
# 예측 결과는 의미 있게 해석하면 안 된다.
# ------------------------------------------------------------

probabilities = torch.softmax(cifar_logits, dim=1)
predictions = torch.argmax(probabilities, dim=1)

print("=== fc 교체 후 예측 결과 일부 ===")

for i in range(5):
    true_id = labels[i].item()
    pred_id = predictions[i].item()
    confidence = probabilities[i, pred_id].item()

    print(
        f"{i}번 이미지 | "
        f"정답: {true_id}({class_names[true_id]}) | "
        f"예측: {pred_id}({class_names[pred_id]}) | "
        f"확신도: {confidence:.4f}"
    )

print()

print("주의:")
print("fc layer는 새로 생성되어 아직 학습되지 않았습니다.")
print("따라서 지금 예측 결과는 정확도 관점에서 의미가 없습니다.")
print()


# ------------------------------------------------------------
# 14. 파라미터 수 계산 함수
# ------------------------------------------------------------

def count_total_parameters(model):
    """
    전체 파라미터 수를 계산한다.
    """

    return sum(
        parameter.numel()
        for parameter in model.parameters()
    )


def count_trainable_parameters(model):
    """
    학습 가능한 파라미터 수를 계산한다.
    requires_grad=True인 파라미터만 계산한다.
    """

    return sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )


def print_parameter_summary(model, title):
    """
    전체 파라미터 수와 학습 가능한 파라미터 수를 출력한다.
    """

    total_params = count_total_parameters(model)
    trainable_params = count_trainable_parameters(model)

    print(f"=== {title} ===")
    print("전체 파라미터 수      :", total_params)
    print("학습 가능한 파라미터 수:", trainable_params)
    print(
        "학습 가능 비율        :",
        f"{trainable_params / total_params * 100:.2f}%"
    )
    print()


print_parameter_summary(
    model=transfer_model,
    title="fc 교체 직후 파라미터 상태",
)


# ------------------------------------------------------------
# 15. 방식 1: Feature Extractor 방식 준비
# ------------------------------------------------------------
# Feature Extractor 방식:
# - pretrained backbone은 고정한다.
# - 마지막 fc layer만 학습한다.
#
# requires_grad=False:
# - 해당 parameter는 학습 중 업데이트되지 않는다.
# ------------------------------------------------------------

feature_extractor_model = resnet18(
    weights=weights,
).to(device)

feature_extractor_model.fc = nn.Linear(
    in_features=feature_extractor_model.fc.in_features,
    out_features=num_classes,
).to(device)

# 전체 파라미터 고정
for param in feature_extractor_model.parameters():
    param.requires_grad = False

# 마지막 fc layer만 학습 가능하게 변경
for param in feature_extractor_model.fc.parameters():
    param.requires_grad = True

print_parameter_summary(
    model=feature_extractor_model,
    title="Feature Extractor 방식 파라미터 상태",
)


# ------------------------------------------------------------
# 16. Feature Extractor 방식에서 학습 가능한 파라미터 이름 확인
# ------------------------------------------------------------

print("=== Feature Extractor 방식에서 학습 가능한 파라미터 ===")

for name, param in feature_extractor_model.named_parameters():
    if param.requires_grad:
        print(name, tuple(param.shape))

print()


# ------------------------------------------------------------
# 17. 방식 2: layer4 + fc Fine-tuning 준비
# ------------------------------------------------------------
# 일부 Fine-tuning:
# - 대부분의 layer는 고정
# - 마지막 block인 layer4와 fc만 학습
# ------------------------------------------------------------

layer4_finetune_model = resnet18(
    weights=weights,
).to(device)

layer4_finetune_model.fc = nn.Linear(
    in_features=layer4_finetune_model.fc.in_features,
    out_features=num_classes,
).to(device)

# 전체 고정
for param in layer4_finetune_model.parameters():
    param.requires_grad = False

# layer4 학습 가능
for param in layer4_finetune_model.layer4.parameters():
    param.requires_grad = True

# fc 학습 가능
for param in layer4_finetune_model.fc.parameters():
    param.requires_grad = True

print_parameter_summary(
    model=layer4_finetune_model,
    title="layer4 + fc Fine-tuning 파라미터 상태",
)


# ------------------------------------------------------------
# 18. layer4 + fc 방식에서 학습 가능한 파라미터 이름 확인
# ------------------------------------------------------------

print("=== layer4 + fc Fine-tuning에서 학습 가능한 파라미터 ===")

for name, param in layer4_finetune_model.named_parameters():
    if param.requires_grad:
        print(name, tuple(param.shape))

print()


# ------------------------------------------------------------
# 19. 방식 3: Full Fine-tuning 준비
# ------------------------------------------------------------
# 전체 Fine-tuning:
# - 모든 layer를 학습 가능하게 둔다.
# - 단, learning rate는 작게 잡는 것이 일반적이다.
# ------------------------------------------------------------

full_finetune_model = resnet18(
    weights=weights,
).to(device)

full_finetune_model.fc = nn.Linear(
    in_features=full_finetune_model.fc.in_features,
    out_features=num_classes,
).to(device)

for param in full_finetune_model.parameters():
    param.requires_grad = True

print_parameter_summary(
    model=full_finetune_model,
    title="Full Fine-tuning 파라미터 상태",
)


# ------------------------------------------------------------
# 20. 방식별 Optimizer 준비 예시
# ------------------------------------------------------------
# 실제 학습은 다음 실습부터 한다.
# 여기서는 optimizer를 어떻게 잡는지 형태만 확인한다.
# ------------------------------------------------------------

# Feature Extractor:
# 학습 가능한 fc 파라미터만 optimizer에 전달
feature_extractor_optimizer = torch.optim.Adam(
    filter(
        lambda param: param.requires_grad,
        feature_extractor_model.parameters(),
    ),
    lr=0.001,
)

# layer4 + fc Fine-tuning:
# layer4와 fc만 학습
layer4_optimizer = torch.optim.Adam(
    filter(
        lambda param: param.requires_grad,
        layer4_finetune_model.parameters(),
    ),
    lr=0.0001,
)

# Full Fine-tuning:
# 전체 학습이므로 더 작은 learning rate 사용
full_finetune_optimizer = torch.optim.Adam(
    full_finetune_model.parameters(),
    lr=0.00001,
)

print("=== Optimizer 준비 완료 ===")
print("Feature Extractor Optimizer:", feature_extractor_optimizer)
print("Layer4 Fine-tuning Optimizer:", layer4_optimizer)
print("Full Fine-tuning Optimizer:", full_finetune_optimizer)
print()


# ------------------------------------------------------------
# 21. 모델 구조 저장용 checkpoint 예시
# ------------------------------------------------------------
# 다음 실습들에서 학습한 모델을 저장할 때
# 아래와 같은 정보를 함께 저장하면 좋다.
# ------------------------------------------------------------

SAVE_DIR = "./saved_models"
os.makedirs(SAVE_DIR, exist_ok=True)

prepare_info = {
    "model_name": "resnet18",
    "pretrained_weights": "ResNet18_Weights.DEFAULT",
    "dataset_name": "CIFAR-10",
    "num_classes": num_classes,
    "class_names": class_names,
    "input_size": [3, 224, 224],
    "imagenet_mean": imagenet_mean,
    "imagenet_std": imagenet_std,
    "transfer_learning_methods": [
        "feature_extractor",
        "layer4_finetuning",
        "full_finetuning",
    ],
}

prepare_info_path = os.path.join(
    SAVE_DIR,
    "transfer_learning_prepare_info.pth",
)

torch.save(
    prepare_info,
    prepare_info_path,
)

print("=== 전이학습 준비 정보 저장 완료 ===")
print("저장 경로:", prepare_info_path)
print()


# ------------------------------------------------------------
# 22. 최종 정리
# ------------------------------------------------------------

print("=== 실습 31 최종 정리 ===")
print("1. pretrained ResNet18 모델을 불러왔다.")
print("2. 기본 ResNet18의 마지막 fc layer는 ImageNet 1000개 class 기준이다.")
print("3. CIFAR-10에 맞게 fc layer를 10개 class 출력으로 교체했다.")
print("4. Feature Extractor 방식은 backbone을 고정하고 fc만 학습한다.")
print("5. layer4 Fine-tuning 방식은 layer4와 fc만 학습한다.")
print("6. Full Fine-tuning 방식은 전체 layer를 학습한다.")
print("7. requires_grad=False이면 해당 파라미터는 학습 중 업데이트되지 않는다.")
print("8. 다음 실습에서는 Feature Extractor 방식으로 실제 학습을 진행한다.")