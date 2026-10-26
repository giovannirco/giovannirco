"""Collect a bounded, public snapshot for the profile renderer."""

import datetime as dt
import json
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError

Count = Annotated[int, Field(ge=0)]
Number = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Fraction = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Payload = dict[str, Any]


def validate_timestamp(value: str) -> str:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.utcoffset() != dt.timedelta(0):
        raise ValueError("timestamps must include UTC timezone")
    return value


Timestamp = Annotated[str, AfterValidator(validate_timestamp)]


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)


class Lab(PublicModel):
    clusters: Count | None = None
    nodes: Count | None = None
    pods: Count | None = None
    cores: Count | None = None
    namespaces: Count | None = None
    updatedAt: Timestamp


class Cluster(PublicModel):
    id: str


class Node(PublicModel):
    cluster: str
    ready: bool | None = None
    cores: Count | None = None
    cpu: Fraction | None = None
    memoryUsed: Number | None = None
    memoryTotal: Number | None = None
    pods: Count | None = None


class Nodes(PublicModel):
    clusters: list[Cluster] = Field(max_length=32)
    nodes: list[Node] = Field(max_length=256)
    updatedAt: Timestamp


class Host(PublicModel):
    reporting: bool
    up: bool | None = None
    cpu: Fraction | None = None
    cores: Count | None = None
    memoryUsed: Number | None = None
    memoryTotal: Number | None = None
    uptimeSeconds: Number | None = None
    vmsTotal: Count | None = None
    vmsRunning: Count | None = None
    containersTotal: Count | None = None
    containersRunning: Count | None = None
    updatedAt: Timestamp | None = None


class Proxmox(PublicModel):
    hosts: list[Host] = Field(max_length=26)
    updatedAt: Timestamp


class Storage(PublicModel):
    disks: Count | None = None
    disksPassing: Count | None = None
    guests: Count | None = None
    backupRuns: Count | None
    backupPassed: Count | None = None
    newestBackup: Timestamp | None = None


class Network(PublicModel):
    flowsPerSecond: Number | None = None
    dropsPerSecond: Number | None = None
    enforcedEndpoints: Count | None = None
    endpoints: Count | None = None
    updatedAt: Timestamp


class Unifi(PublicModel):
    reporting: bool
    devices: Count | None = None
    online: Count | None = None
    aps: Count | None = None
    apsOnline: Count | None = None
    switches: Count | None = None
    switchesOnline: Count | None = None
    gateways: Count | None = None
    gatewaysOnline: Count | None = None
    internetUp: bool | None = None
    latencyMs: Number | None = None
    downloadBytes: Number | None = None
    uploadBytes: Number | None = None
    updatedAt: Timestamp | None = None


class Gpu(PublicModel):
    reporting: bool
    usage: Fraction | None = None
    memoryUsed: Number | None = None
    memoryTotal: Number | None = None
    temperature: Number | None = None
    power: Number | None = None
    powerLimit: Number | None = None
    updatedAt: Timestamp | None = None
    history: list[tuple[Number, Fraction | None]] = Field(default_factory=list, max_length=120)


class Gpus(PublicModel):
    gpus: list[Gpu] = Field(max_length=16)
    start: Number | None = None
    end: Number | None = None


class Repository(PublicModel):
    name: str
    stargazerCount: Count
    pushedAt: Timestamp | None
    primaryLanguage: dict[str, str] | None


class Day(PublicModel):
    date: dt.date
    contributionCount: Count


class Week(PublicModel):
    firstDay: dt.date
    contributionDays: list[Day] = Field(max_length=7)


class Calendar(PublicModel):
    totalContributions: Count
    weeks: list[Week] = Field(max_length=54)


class Sample(PublicModel):
    data: Payload
    collected_at: Timestamp
    stale: bool = False


MODELS: dict[str, type[PublicModel]] = {
    "lab": Lab,
    "nodes": Nodes,
    "proxmox": Proxmox,
    "storage": Storage,
    "network": Network,
    "unifi": Unifi,
    "gpu": Gpus,
}


def normalize(name: str, payload: object) -> Payload:
    result = MODELS[name].model_validate(payload).model_dump(mode="json")
    items = result.get("hosts", result.get("gpus", [result] if name == "unifi" else []))
    for item in items:
        if item.get("reporting") is False:
            for key in item:
                if key not in ("reporting", "updatedAt"):
                    item[key] = [] if key == "history" else None
    return result


def cluster_states(data: Payload) -> list[str]:
    states = []
    for cluster in data["clusters"]:
        ready = [node["ready"] for node in data["nodes"] if node["cluster"] == cluster["id"]]
        if False in ready:
            states.append("degraded")
        elif not ready or None in ready:
            states.append("unknown")
        else:
            states.append("ready")
    return states


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def parse_github(payload: Payload, featured: Sequence[str]) -> Payload:
    if payload.get("errors"):
        raise ValueError("GraphQL returned errors")
    try:
        user = payload["data"]["user"]
        repositories = [Repository.model_validate(item) for item in user["repositories"]["nodes"]]
        calendar = Calendar.model_validate(user["contributionsCollection"]["contributionCalendar"])
    except (KeyError, TypeError) as error:
        raise ValueError("GraphQL response is incomplete") from error
    repos = {
        repo.name: {
            "stars": repo.stargazerCount,
            "pushed_at": repo.pushedAt,
            "language": repo.primaryLanguage.get("name") if repo.primaryLanguage else None,
        }
        for repo in repositories
        if repo.name in featured
    }
    if set(featured) - repos.keys():
        raise ValueError("featured repository missing from GraphQL response")
    return {
        "repos": repos,
        "total": calendar.totalContributions,
        "weeks": [
            {"date": week.firstDay.isoformat(), "count": sum(day.contributionCount for day in week.contributionDays)}
            for week in calendar.weeks
        ],
    }


def request_json(url: str, token: str | None = None, body: Payload | None = None) -> Payload:
    headers = {"User-Agent": "giovannirco-profile", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("source response exceeds size limit")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("expected a JSON object")
    return result


def collect(
    names: Sequence[str],
    previous: dict[str, Sample],
    fetch: Callable[[str], Payload],
    now: dt.datetime,
) -> tuple[dict[str, Sample], list[str]]:
    samples: dict[str, Sample] = {}
    failures = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        pending = {name: executor.submit(fetch, name) for name in names}
        for name, future in pending.items():
            try:
                payload = future.result()
                data = payload if name == "github" else normalize(name, payload)
                samples[name] = Sample(data=data, collected_at=now.isoformat())
            except OSError, ValueError, ValidationError:
                failures.append(name)
                if name in previous:
                    samples[name] = previous[name].model_copy(update={"stale": True})
    return samples, failures


GITHUB_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes { name stargazerCount pushedAt primaryLanguage { name } }
      pageInfo { hasNextPage }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { firstDay contributionDays { date contributionCount } }
      }
    }
  }
}
"""
