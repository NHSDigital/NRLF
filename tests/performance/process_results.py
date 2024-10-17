# flake8: noqa
from csv import DictReader
from statistics import mean

import fire
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel


class K6OutputRow(BaseModel):
    metric_name: str
    timestamp: int
    metric_value: float
    scenario: str
    error: str | None
    error_code: str | None
    status: str | None
    expected_response: str


def _load_rows(file_path):
    with open(file_path, "r") as file:
        csv_reader = DictReader(file)
        for row in csv_reader:
            yield K6OutputRow.model_validate(row)


def _load_k6_output(file_path: str):
    data = {}
    vus = []
    metrics_to_capture = [
        "http_reqs",
        "iterations",
        "http_req_duration",
        "http_req_blocked",
        "http_req_connecting",
        "http_req_tls_handshaking",
        "http_req_sending",
        "http_req_waiting",
        "http_req_receiving",
        "checks",
    ]

    for row in _load_rows(file_path):
        if row.metric_name == "vus":
            vus.append(row)
            continue

        if row.metric_name not in metrics_to_capture:
            continue

        if row.scenario not in data:
            data[row.scenario] = {}

        if row.timestamp not in data[row.scenario]:
            data[row.scenario][row.timestamp] = {}

        if row.metric_name not in data[row.scenario][row.timestamp]:
            data[row.scenario][row.timestamp][row.metric_name] = []

        data[row.scenario][row.timestamp][row.metric_name].append(row)

    return {"scenarios": data, "vus": vus}


def _create_response_count_figure(data: dict, title: str):
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(title)
    fig_labels = set(["Successful Requests"])

    for scenario in data.values():
        for metrics in scenario.values():
            failures = [
                row
                for row in metrics["http_req_duration"]
                if row.expected_response == "false"
            ]
            for failure in failures:
                fig_labels.add(f"Failure - Status Code {failure.status}")

    for index, scenario in enumerate(data.keys()):
        axes = fig.add_subplot(2, 2, index + 1)
        scenario_data = data[scenario]

        timestamps = []
        successful_requests = []
        failed_requests = []
        failure_plots = []

        for timestamp, metrics in scenario_data.items():
            timestamps.append(timestamp)
            successes = [
                row
                for row in metrics["http_req_duration"]
                if row.expected_response == "true"
            ]
            failures = [
                row
                for row in metrics["http_req_duration"]
                if row.expected_response == "false"
            ]

            successful_requests.append(len(successes))
            if not failures:
                failed_requests.append(None)
                continue

            failure_dict = {}
            for failure in failures:
                failure_name = f"Failure - Status Code {failure.status}"
                if failure_name not in failed_requests:
                    failure_dict[failure_name] = 0

                failure_dict[failure_name] += 1

            failed_requests.append(failure_dict)

        first_timestamp = min(timestamps)

        x = np.array([timestamp - first_timestamp for timestamp in timestamps])
        failure_labels = set()

        for failed_request in filter(lambda x: x is not None, failed_requests):
            failure_labels.update(failed_request.keys())

        failure_plots = [
            np.array(
                [failure.get(label) if failure else 0 for failure in failed_requests]
            )
            for label in failure_labels
        ]

        axes.stackplot(
            x, np.array(successful_requests), *failure_plots, labels=list(fig_labels)
        )
        axes.grid()
        axes.set_title(scenario)
        axes.set_xlabel("Time (s)")
        axes.set_ylabel("Requests per Second")
        axes.axis("tight")

    fig.legend(list(fig_labels), loc="upper left")
    return fig, failure_plots


def _create_response_time_figure(data: dict, title: str):
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(title)

    for index, scenario in enumerate(data.keys()):
        axes = fig.add_subplot(2, 2, index + 1)
        scenario_data = data[scenario]

        timestamps = []
        http_req_blocked = []
        http_req_connecting = []
        http_req_tls_handshaking = []
        http_req_sending = []
        http_req_waiting = []
        http_req_receiving = []

        for timestamp, metrics in scenario_data.items():
            timestamps.append(timestamp)
            http_req_blocked.append(
                mean([row.metric_value for row in metrics["http_req_blocked"]])
            )
            http_req_connecting.append(
                mean([row.metric_value for row in metrics["http_req_connecting"]])
            )
            http_req_tls_handshaking.append(
                mean([row.metric_value for row in metrics["http_req_tls_handshaking"]])
            )
            http_req_sending.append(
                mean([row.metric_value for row in metrics["http_req_sending"]])
            )
            http_req_waiting.append(
                mean([row.metric_value for row in metrics["http_req_waiting"]])
            )
            http_req_receiving.append(
                mean([row.metric_value for row in metrics["http_req_receiving"]])
            )

        first_timestamp = min(timestamps)

        x = np.array([timestamp - first_timestamp for timestamp in timestamps])
        axes.stackplot(
            x,
            np.array(http_req_blocked),
            np.array(http_req_connecting),
            np.array(http_req_tls_handshaking),
            np.array(http_req_sending),
            np.array(http_req_waiting),
            np.array(http_req_receiving),
            labels=[
                "http_req_blocked",
                "http_req_connecting",
                "http_req_tls_handshaking",
                "http_req_sending",
                "http_req_waiting",
                "http_req_receiving",
            ],
        )
        axes.grid()
        axes.set_title(scenario)
        axes.set_xlabel("Time (s)")
        axes.set_ylabel("Duration (ms)")
        axes.axis("tight")

    fig.legend(
        [
            "http_req_blocked",
            "http_req_connecting",
            "http_req_tls_handshaking",
            "http_req_sending",
            "http_req_waiting",
            "http_req_receiving",
        ],
        loc="upper left",
    )
    return fig


def _split_ramp_up_data_by_rps(data, target_rps):
    # Split into ramp-up and baseline
    ramp_up_data = {}
    baseline_data = {}

    for scenario, scenario_data in data.items():
        sorted_timestamps = sorted(scenario_data.keys())
        ramp_up_data[scenario] = {}
        baseline_data[scenario] = {}
        ramp_up = True

        for index, timestamp in enumerate(sorted_timestamps):
            data = scenario_data[timestamp]
            iterations = data["iterations"]
            previous_iterations = None

            if ramp_up is False:
                baseline_data[scenario][timestamp] = data
                continue

            if index > 0:
                previous_iterations = scenario_data[sorted_timestamps[index - 1]][
                    "iterations"
                ]

            if (
                len(iterations) >= target_rps
                and previous_iterations
                and len(previous_iterations) >= target_rps
            ):
                ramp_up = False
                baseline_data[scenario][timestamp] = data
                continue

            ramp_up_data[scenario][timestamp] = data

    return ramp_up_data, baseline_data


def _split_ramp_up_data_by_vus(data, vus, target_vus):
    # Split into ramp-up and baseline
    ramp_up_data = {}
    baseline_data = {}
    scenario_count = len(data.keys())

    for scenario, scenario_data in data.items():
        sorted_timestamps = sorted(scenario_data.keys())
        ramp_up_data[scenario] = {}
        baseline_data[scenario] = {}
        ramp_end_timestamp = None

        for vu in vus:
            if vu.metric_value >= target_vus * scenario_count:
                ramp_end_timestamp = vu.timestamp
                break

        for timestamp in sorted_timestamps:
            if timestamp >= ramp_end_timestamp:
                baseline_data[scenario][timestamp] = scenario_data[timestamp]
                continue

            ramp_up_data[scenario][timestamp] = scenario_data[timestamp]

    return ramp_up_data, baseline_data


def baseline(
    file_path: str,
    target_rps: int = 5,
):
    output = _load_k6_output(file_path)
    scenarios = output["scenarios"]

    ramp_up_data, baseline_data = _split_ramp_up_data_by_rps(scenarios, target_rps)

    fig = _create_response_time_figure(
        baseline_data,
        f"NRL v3.0 Consumer API - Baseline Performance ({target_rps} RPS - Warm Start) - HTTP Response Times (ms)",
    )
    fig.savefig("dist/baseline_performance.png")

    fig = _create_response_time_figure(
        ramp_up_data,
        f"NRL v3.0 Consumer API - Ramp-Up Performance (Up to {target_rps} RPS - Cold Start) - HTTP Response Times (ms)",
    )
    fig.savefig("dist/ramp_up_performance.png")

    fig, baseline_failures = _create_response_count_figure(
        baseline_data,
        f"NRL v3.0 Consumer API - Baseline Performance ({target_rps} RPS - Warm Start) - Response Count",
    )
    fig.savefig("dist/baseline_count.png")

    fig, ramp_up_failures = _create_response_count_figure(
        ramp_up_data,
        f"NRL v3.0 Consumer API - Ramp-Up Performance (Up to {target_rps} RPS - Cold Start) - Response Count",
    )
    fig.savefig("dist/ramp_up_count.png")
    if len(baseline_failures) > 0 or len(ramp_up_failures) > 0:
        print(
            f"Number of Failure Responses: {len(baseline_failures) + len(ramp_up_failures)}"
        )
        exit(1)


def stress(
    file_path: str,
    target_vus: int = 10,
):
    data_per_endpoint = _load_k6_output(file_path)
    scenarios = data_per_endpoint["scenarios"]
    vus = data_per_endpoint["vus"]

    ramp_up_data, baseline_data = _split_ramp_up_data_by_vus(scenarios, vus, target_vus)

    fig = _create_response_time_figure(
        baseline_data,
        f"NRL v3.0 Consumer API - Stress Performance ({target_vus} VUs - Warm Start) - HTTP Response Times (ms)",
    )
    fig.savefig("dist/stress_baseline_performance.png")

    fig = _create_response_time_figure(
        ramp_up_data,
        f"NRL v3.0 Consumer API - Stress Performance (Up to {target_vus} VUs - Cold Start) - HTTP Response Times (ms)",
    )
    fig.savefig("dist/stress_ramp_up_performance.png")

    fig, baseline_failures = _create_response_count_figure(
        baseline_data,
        f"NRL v3.0 Consumer API - Stress Performance ({target_vus} VUs - Warm Start) - Response Count",
    )
    fig.savefig("dist/stress_baseline_count.png")

    fig, ramp_up_failures = _create_response_count_figure(
        ramp_up_data,
        f"NRL v3.0 Consumer API - Stress Performance (Up to {target_vus} VUs - Cold Start) - Response Count",
    )
    fig.savefig("dist/stress_ramp_up_count.png")
    if len(baseline_failures) > 0 or len(ramp_up_failures) > 0:
        print(
            f"Number of Failure Responses: {len(baseline_failures) + len(ramp_up_failures)}"
        )
        exit(1)


if __name__ == "__main__":
    fire.Fire()
