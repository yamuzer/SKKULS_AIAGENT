import csv
from pathlib import Path
from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

CSV_PATH = (
    BASE_DIR
    / "data"
    / "shipment_quality_650.csv"
)


class GraphState(TypedDict):

    shipment_id: str

    center_name: str
    product_group: str

    quality_score: int
    target_score: int

    defect_count: int
    main_defect: str
    correction_gain: int

    retry_count: int
    max_retries: int

    status: str
    result: str


def load_rows() -> list[dict]:

    with CSV_PATH.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        return list(
            csv.DictReader(
                csv_file
            )
        )


ROWS = load_rows()


def find_shipment(
    shipment_id: str
) -> dict:

    for row in ROWS:

        if (
            row["shipment_id"]
            == shipment_id
        ):
            return row

    raise ValueError(
        f"shipment_id를 찾을 수 없습니다: "
        f"{shipment_id}"
    )


def load_shipment(
    state: GraphState
):

    print(
        "\n[load_shipment 실행]"
    )

    shipment_id = (
        state["shipment_id"]
    )

    row = find_shipment(
        shipment_id
    )

    print(
        f"출고 ID: {shipment_id}"
    )

    print(
        f"센터: {row['center_name']}"
    )

    print(
        f"상품군: {row['product_group']}"
    )

    return {
        "center_name":
            row["center_name"],

        "product_group":
            row["product_group"],

        "quality_score":
            int(
                row[
                    "initial_quality_score"
                ]
            ),

        "target_score":
            int(
                row[
                    "target_quality_score"
                ]
            ),

        "defect_count":
            int(
                row[
                    "defect_count"
                ]
            ),

        "main_defect":
            row["main_defect"],

        "correction_gain":
            int(
                row[
                    "correction_gain"
                ]
            ),

        "retry_count": 0,

        "max_retries":
            int(
                row[
                    "max_retries"
                ]
            ),

        "status": "loaded",
    }


def quality_check(
    state: GraphState
):

    print(
        "\n[quality_check 실행]"
    )

    print(
        f"현재 품질점수: "
        f"{state['quality_score']}"
    )

    print(
        f"목표 품질점수: "
        f"{state['target_score']}"
    )

    print(
        f"재시도 횟수: "
        f"{state['retry_count']} "
        f"/ {state['max_retries']}"
    )

    print(
        f"주요 불량: "
        f"{state['main_defect']}"
    )

    return {
        "status": "checking"
    }


def route_quality(
    state: GraphState
):

    print(
        "\n[route_quality 실행]"
    )

    quality_score = (
        state["quality_score"]
    )

    target_score = (
        state["target_score"]
    )

    retry_count = (
        state["retry_count"]
    )

    max_retries = (
        state["max_retries"]
    )

    if (
        quality_score
        >= target_score
    ):

        print(
            "판정: pass"
        )

        return "pass"

    if (
        retry_count
        >= max_retries
    ):

        print(
            "판정: failed"
        )

        return "failed"

    print(
        "판정: retry"
    )

    return "retry"


def correction(
    state: GraphState
):

    print(
        "\n[correction 실행]"
    )

    current_score = (
        state["quality_score"]
    )

    gain = (
        state["correction_gain"]
    )

    defect_count = (
        state["defect_count"]
    )

    correction_value = (
        gain
        - defect_count // 2
    )

    correction_value = max(
        correction_value,
        1,
    )

    new_score = min(
        100,
        current_score
        + correction_value,
    )

    new_retry_count = (
        state["retry_count"]
        + 1
    )

    print(
        f"보정 전 점수: "
        f"{current_score}"
    )

    print(
        f"보정 증가량: "
        f"{correction_value}"
    )

    print(
        f"보정 후 점수: "
        f"{new_score}"
    )

    return {
        "quality_score":
            new_score,

        "retry_count":
            new_retry_count,

        "status":
            "corrected",
    }


def approved(
    state: GraphState
):

    print(
        "\n[approved 실행]"
    )

    result = (
        f"출고 승인: "
        f"{state['shipment_id']}은 "
        f"품질점수 "
        f"{state['quality_score']}점으로 "
        f"목표점수 "
        f"{state['target_score']}점을 "
        f"충족했습니다."
    )

    return {
        "status": "approved",
        "result": result,
    }


def rejected(
    state: GraphState
):

    print(
        "\n[rejected 실행]"
    )

    result = (
        f"출고 보류: "
        f"{state['shipment_id']} / "
        f"최종 품질점수 "
        f"{state['quality_score']}점 / "
        f"목표 "
        f"{state['target_score']}점 / "
        f"시도 횟수 "
        f"{state['retry_count']}회 / "
        f"주요 불량 "
        f"{state['main_defect']}"
    )

    return {
        "status": "rejected",
        "result": result,
    }


builder = StateGraph(
    GraphState
)


builder.add_node(
    "load_shipment",
    load_shipment,
)

builder.add_node(
    "quality_check",
    quality_check,
)

builder.add_node(
    "correction",
    correction,
)

builder.add_node(
    "approved",
    approved,
)

builder.add_node(
    "rejected",
    rejected,
)


builder.add_edge(
    START,
    "load_shipment",
)

builder.add_edge(
    "load_shipment",
    "quality_check",
)


builder.add_conditional_edges(
    "quality_check",
    route_quality,
    {
        "pass":
            "approved",

        "retry":
            "correction",

        "failed":
            "rejected",
    },
)


builder.add_edge(
    "correction",
    "quality_check",
)


builder.add_edge(
    "approved",
    END,
)

builder.add_edge(
    "rejected",
    END,
)


graph = builder.compile()


def run_shipment(
    shipment_id: str
) -> None:

    print(
        "\n"
        + "#" * 80
    )

    print(
        f"실행 shipment_id: "
        f"{shipment_id}"
    )

    print(
        "#" * 80
    )

    initial_state: GraphState = {
        "shipment_id":
            shipment_id,

        "center_name":
            "",

        "product_group":
            "",

        "quality_score":
            0,

        "target_score":
            0,

        "defect_count":
            0,

        "main_defect":
            "",

        "correction_gain":
            0,

        "retry_count":
            0,

        "max_retries":
            0,

        "status":
            "ready",

        "result":
            "",
    }


    result = graph.invoke(
        initial_state
    )


    print(
        "\n최종 State"
    )

    print(
        result
    )


    print(
        "\n최종 결과:"
    )

    print(
        result["result"]
    )


if __name__ == "__main__":

    run_shipment(
        "SHP-0047"
    )

    # 추가 테스트
    #
    # run_shipment("SHP-0118")
    # run_shipment("SHP-0275")
    # run_shipment("SHP-0499")
