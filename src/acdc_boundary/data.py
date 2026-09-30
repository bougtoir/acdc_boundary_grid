import json
import math
import warnings
from dataclasses import dataclass, replace

import networkx as nx
import numpy as np
import pandas as pd
import simbench as sb

from .paths import DATA_INTERIM, DATA_PROCESSED, DATA_RAW


@dataclass(frozen=True)
class Edge:
    parent: int
    child: int
    length_km: float
    r_ohm_per_km: float
    max_i_a: float
    downstream_energy_kwh: float
    downstream_peak_kw: float
    loss_hours: float
    x_ohm_per_km: float = 0.08


@dataclass(frozen=True)
class Feeder:
    name: str
    code: str
    topology: str
    root: int
    nodes: tuple[int, ...]
    children: dict[int, tuple[int, ...]]
    node_energy_kwh: dict[int, float]
    node_peak_kw: dict[int, float]
    coordinates: dict[int, tuple[float, float]]
    edges: dict[tuple[int, int], Edge]


def _coordinates(net, nodes: set[int]) -> dict[int, tuple[float, float]]:
    coordinates = {}
    for node in nodes:
        value = net.bus.at[node, "geo"]
        parsed = json.loads(value)
        lon, lat = parsed["coordinates"]
        coordinates[node] = (float(lon), float(lat))
    return coordinates


def _distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
    y = lat2 - lat1
    return 6371.0 * math.sqrt(x * x + y * y)


def _orient(graph: nx.Graph, root: int) -> tuple[dict[int, tuple[int, ...]], list[tuple[int, int]]]:
    tree = nx.bfs_tree(graph, root)
    children = {node: tuple(int(v) for v in tree.successors(node)) for node in tree.nodes}
    edges = [(int(u), int(v)) for u, v in tree.edges]
    return children, edges


def _subtree_nodes(children: dict[int, tuple[int, ...]], node: int) -> tuple[int, ...]:
    values = [node]
    for child in children[node]:
        values.extend(_subtree_nodes(children, child))
    return tuple(values)


def load_feeder(name: str, code: str, topology: str = "original") -> Feeder:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        net = sb.get_simbench_net(code)
        profiles = sb.get_absolute_values(net, profiles_instead_of_study_cases=True)[
            ("load", "p_mw")
        ]
    root = int(net.trafo.iloc[0].lv_bus)
    original = nx.Graph()
    line_lookup = {}
    for index, row in net.line[net.line.in_service.astype(bool)].iterrows():
        u, v = int(row.from_bus), int(row.to_bus)
        original.add_edge(u, v)
        line_lookup[frozenset((u, v))] = int(index)
    component = set(nx.node_connected_component(original, root))
    original = original.subgraph(component).copy()
    coordinates = _coordinates(net, component)
    if topology == "original":
        graph = original
        calibration = 1.0
    elif topology == "synthetic_mst":
        complete = nx.Graph()
        for i, u in enumerate(sorted(component)):
            for v in sorted(component)[i + 1 :]:
                complete.add_edge(u, v, weight=_distance_km(coordinates[u], coordinates[v]))
        graph = nx.minimum_spanning_tree(complete, weight="weight")
        ratios = []
        for u, v in original.edges:
            line = net.line.loc[line_lookup[frozenset((u, v))]]
            distance = _distance_km(coordinates[u], coordinates[v])
            if distance > 0:
                ratios.append(float(line.length_km) / distance)
        calibration = float(np.median(ratios))
    else:
        raise ValueError(topology)
    children, oriented_edges = _orient(graph, root)
    nodes = tuple(sorted(component))
    bus_profiles = {node: np.zeros(len(profiles), dtype=float) for node in nodes}
    for load_index, load in net.load.iterrows():
        bus = int(load.bus)
        if bus in component and load_index in profiles.columns:
            bus_profiles[bus] += profiles[load_index].to_numpy(dtype=float) * 1000.0
    node_energy = {node: float(values.sum() * 0.25) for node, values in bus_profiles.items()}
    node_peak = {node: float(values.max(initial=0.0)) for node, values in bus_profiles.items()}
    median_r = float(net.line.r_ohm_per_km.median())
    median_x = float(net.line.x_ohm_per_km.median())
    median_i_a = float(net.line.max_i_ka.median() * 1000.0)
    edge_records = {}
    for parent, child in oriented_edges:
        descendants = _subtree_nodes(children, child)
        downstream = np.sum([bus_profiles[node] for node in descendants], axis=0)
        peak = float(downstream.max(initial=0.0))
        energy = float(downstream.sum() * 0.25)
        loss_hours = float(np.square(downstream / peak).sum() * 0.25) if peak > 0 else 0.0
        key = frozenset((parent, child))
        if topology == "original":
            line = net.line.loc[line_lookup[key]]
            length = float(line.length_km)
            resistance = float(line.r_ohm_per_km)
            reactance = float(line.x_ohm_per_km)
            max_i = float(line.max_i_ka * 1000.0)
        else:
            length = _distance_km(coordinates[parent], coordinates[child]) * calibration
            resistance = median_r
            reactance = median_x
            max_i = median_i_a
        edge_records[(parent, child)] = Edge(
            parent=parent,
            child=child,
            length_km=length,
            r_ohm_per_km=resistance,
            max_i_a=max_i,
            downstream_energy_kwh=energy,
            downstream_peak_kw=peak,
            loss_hours=loss_hours,
            x_ohm_per_km=reactance,
        )
    return Feeder(
        name=name,
        code=code,
        topology=topology,
        root=root,
        nodes=nodes,
        children=children,
        node_energy_kwh=node_energy,
        node_peak_kw=node_peak,
        coordinates=coordinates,
        edges=edge_records,
    )


def native_dc_allocation(feeder: Feeder, share: float, seed: int) -> dict[int, float]:
    rng = np.random.default_rng(seed)
    nodes = [node for node in feeder.nodes if node != feeder.root]
    rng.shuffle(nodes)
    total = sum(feeder.node_energy_kwh[node] for node in nodes)
    target = share * total
    allocation = {node: 0.0 for node in feeder.nodes}
    accumulated = 0.0
    for node in nodes:
        energy = feeder.node_energy_kwh[node]
        if accumulated >= target or energy <= 0:
            continue
        fraction = min(1.0, (target - accumulated) / energy)
        allocation[node] = fraction
        accumulated += energy * fraction
    return allocation


def ev_data_summary() -> pd.DataFrame:
    path = DATA_RAW / "ev_charging/22495141_v1/ChargingRecords.csv"
    frame = pd.read_csv(path)
    frame["duration_from_timestamps_min"] = (
        pd.to_datetime(frame["EndDatetime"]) - pd.to_datetime(frame["StartDatetime"])
    ).dt.total_seconds() / 60.0
    frame["valid"] = (
        frame["Duration"].gt(0)
        & frame["duration_from_timestamps_min"].gt(0)
        & frame["Demand"].ge(0)
    )
    valid = frame[frame.valid].copy()
    valid["average_kw"] = valid["Demand"] / (valid["Duration"] / 60.0)
    summary = pd.DataFrame(
        [
            {
                "records_total": len(frame),
                "records_valid": len(valid),
                "records_excluded": len(frame) - len(valid),
                "median_energy_kwh": valid.Demand.median(),
                "median_duration_min": valid.Duration.median(),
                "median_reconstructed_kw": valid.average_kw.median(),
                "p95_reconstructed_kw": valid.average_kw.quantile(0.95),
            }
        ]
    )
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    summary.to_csv(DATA_PROCESSED / "ev_charging_summary.csv", index=False)
    return summary


def export_feeder(feeder: Feeder) -> None:
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    stem = f"{feeder.name}_{feeder.topology}"
    pd.DataFrame(
        [
            {
                "node": node,
                "energy_kwh": feeder.node_energy_kwh[node],
                "peak_kw": feeder.node_peak_kw[node],
                "longitude": feeder.coordinates[node][0],
                "latitude": feeder.coordinates[node][1],
            }
            for node in feeder.nodes
        ]
    ).to_csv(DATA_INTERIM / f"{stem}_nodes.csv", index=False)
    pd.DataFrame([edge.__dict__ for edge in feeder.edges.values()]).to_csv(
        DATA_INTERIM / f"{stem}_edges.csv", index=False
    )


def scaled_edge(edge: Edge, energy_factor: float, peak_factor: float) -> Edge:
    return replace(
        edge,
        downstream_energy_kwh=edge.downstream_energy_kwh * energy_factor,
        downstream_peak_kw=edge.downstream_peak_kw * peak_factor,
    )
