from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from typing import Any

OBSERVED_ON = "2026-03-24"

SERVICE_BASE_URLS = {
    "data": "https://data.rcsb.org",
    "search": "https://search.rcsb.org",
    "model": "https://models.rcsb.org",
    "volume": "https://maps.rcsb.org",
    "sequence": "https://sequence-coordinates.rcsb.org",
    "alignment": "https://alignment.rcsb.org/structures",
}

SERVICE_ENV_VARS = {
    "data": "PDB_DATA_BASE_URL",
    "search": "PDB_SEARCH_BASE_URL",
    "model": "PDB_MODEL_BASE_URL",
    "volume": "PDB_VOLUME_BASE_URL",
    "sequence": "PDB_SEQUENCE_BASE_URL",
    "alignment": "PDB_ALIGNMENT_BASE_URL",
}

SERVICE_SOURCES = {
    "data": "https://data.rcsb.org/index.html",
    "search": "https://search.rcsb.org/",
    "model": "https://models.rcsb.org/openapi.json",
    "volume": "https://maps.rcsb.org/openapi.json",
    "sequence": "https://sequence-coordinates.rcsb.org/",
    "alignment": "https://alignment.rcsb.org/",
}

SERVICE_SEMANTICS = {
    "data": (
        "Authoritative structure metadata and annotations for PDB entries and selected computed "
        "structure models. Use this when you already know the identifiers you need."
    ),
    "search": (
        "Archive-wide discovery API. Use this to find identifiers, counts, facets, and grouped "
        "hits before drilling into the Data API."
    ),
    "model": (
        "Coordinate subset API for structural models. Use this to pull whole structures or "
        "geometry-focused subsets such as assemblies, ligands, interactions, and atom selections."
    ),
    "volume": (
        "Volumetric density subset API for crystallographic and EM maps. Use this for whole-cell "
        "or bounded-region density retrieval."
    ),
    "sequence": (
        "Sequence-to-structure alignment and positional annotation graph. Use this when moving "
        "between PDB chains, UniProt, RefSeq, and genome coordinates."
    ),
    "alignment": (
        "Asynchronous structure superposition jobs. Use this for pairwise structural alignment and "
        "to poll for computed alignment results."
    ),
}


@dataclass(frozen=True)
class ParameterDoc:
    name: str
    location: str
    required: bool
    description: str
    schema_type: str | None = None


@dataclass(frozen=True)
class EndpointDoc:
    operation_key: str
    service: str
    method: str
    path: str
    summary: str
    semantic_kind: str
    semantic_summary: str
    source_url: str
    path_parameters: tuple[ParameterDoc, ...] = ()
    query_parameters: tuple[ParameterDoc, ...] = ()
    request_body_required: bool = False
    request_body_content_types: tuple[str, ...] = ()
    response_content_types: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path_parameters"] = [asdict(item) for item in self.path_parameters]
        payload["query_parameters"] = [asdict(item) for item in self.query_parameters]
        payload["base_url"] = base_url_for_service(self.service)
        return payload


def base_url_for_service(service: str) -> str:
    return os.environ.get(SERVICE_ENV_VARS[service], SERVICE_BASE_URLS[service]).rstrip("/")


def collection_summary() -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "base_url": base_url_for_service(name),
            "source_url": SERVICE_SOURCES[name],
            "semantic_scope": SERVICE_SEMANTICS[name],
        }
        for name in SERVICE_BASE_URLS
    ]


def available_operation_keys() -> tuple[str, ...]:
    return tuple(item.operation_key for item in endpoint_docs())


def endpoint_docs() -> tuple[EndpointDoc, ...]:
    docs = [
        *_build_data_docs(),
        *_build_search_docs(),
        *_build_model_docs(),
        *_build_volume_docs(),
        *_build_sequence_docs(),
        *_build_alignment_docs(),
    ]
    return tuple(
        sorted(docs, key=lambda item: (item.service, item.path, item.method, item.operation_key))
    )


def filter_endpoint_docs(selector: str) -> tuple[EndpointDoc, ...]:
    if selector == "all":
        return endpoint_docs()
    matches = [
        item
        for item in endpoint_docs()
        if selector == item.operation_key
        or selector == item.service
        or selector == item.path
        or selector in item.operation_key
        or selector in item.path
        or selector in item.summary.lower()
    ]
    return tuple(matches)


def _build_data_docs() -> list[EndpointDoc]:
    docs = [
        _data_rest_doc("data.assembly", "/core/assembly/{entry_id}/{assembly_id}"),
        _data_rest_doc("data.branched-entity", "/core/branched_entity/{entry_id}/{entity_id}"),
        _data_rest_doc(
            "data.branched-entity-instance", "/core/branched_entity_instance/{entry_id}/{asym_id}"
        ),
        _data_rest_doc("data.chemcomp", "/core/chemcomp/{comp_id}"),
        _data_rest_doc("data.drugbank", "/core/drugbank/{comp_id}"),
        _data_rest_doc("data.entry", "/core/entry/{entry_id}"),
        _data_rest_doc("data.entry-group", "/core/entry_groups/{group_id}"),
        _data_rest_doc("data.group-provenance", "/core/group_provenance/{group_provenance_id}"),
        _data_rest_doc("data.interface", "/core/interface/{entry_id}/{assembly_id}/{interface_id}"),
        _data_rest_doc("data.nonpolymer-entity", "/core/nonpolymer_entity/{entry_id}/{entity_id}"),
        _data_rest_doc("data.nonpolymer-entity-group", "/core/nonpolymer_entity_groups/{group_id}"),
        _data_rest_doc(
            "data.nonpolymer-entity-instance",
            "/core/nonpolymer_entity_instance/{entry_id}/{asym_id}",
        ),
        _data_rest_doc("data.polymer-entity", "/core/polymer_entity/{entry_id}/{entity_id}"),
        _data_rest_doc("data.polymer-entity-group", "/core/polymer_entity_groups/{group_id}"),
        _data_rest_doc(
            "data.polymer-entity-instance", "/core/polymer_entity_instance/{entry_id}/{asym_id}"
        ),
        _data_rest_doc("data.pubmed", "/core/pubmed/{entry_id}"),
        _data_rest_doc("data.uniprot", "/core/uniprot/{entry_id}/{entity_id}"),
        _data_rest_doc("data.holdings-current-ccd-ids", "/holdings/current/ccd_ids"),
        _data_rest_doc("data.holdings-current-entry-ids", "/holdings/current/entry_ids"),
        _data_rest_doc("data.holdings-current-prd-ids", "/holdings/current/prd_ids"),
        _data_rest_doc("data.holdings-removed-entry-ids", "/holdings/removed/entry_ids"),
        _data_rest_doc("data.holdings-removed-entry", "/holdings/removed/{entry_id}"),
        _data_rest_doc("data.holdings-status", "/holdings/status"),
        _data_rest_doc("data.holdings-status-entry", "/holdings/status/{entry_id}"),
        _data_rest_doc("data.holdings-unreleased", "/holdings/unreleased"),
        _data_rest_doc("data.holdings-unreleased-entry-ids", "/holdings/unreleased/entry_ids"),
        _data_rest_doc("data.holdings-unreleased-entry", "/holdings/unreleased/{entry_id}"),
        _data_rest_doc("data.schema-assembly", "/schema/assembly"),
        _data_rest_doc("data.schema-branched-entity", "/schema/branched_entity"),
        _data_rest_doc("data.schema-branched-entity-instance", "/schema/branched_entity_instance"),
        _data_rest_doc("data.schema-chemcomp", "/schema/chem_comp"),
        _data_rest_doc("data.schema-drugbank", "/schema/drugbank"),
        _data_rest_doc("data.schema-entry", "/schema/entry"),
        _data_rest_doc("data.schema-nonpolymer-entity", "/schema/nonpolymer_entity"),
        _data_rest_doc(
            "data.schema-nonpolymer-entity-instance", "/schema/nonpolymer_entity_instance"
        ),
        _data_rest_doc("data.schema-polymer-entity", "/schema/polymer_entity"),
        _data_rest_doc("data.schema-polymer-entity-instance", "/schema/polymer_entity_instance"),
        _data_rest_doc("data.schema-pubmed", "/schema/pubmed"),
        _data_rest_doc("data.schema-uniprot", "/schema/uniprot"),
    ]
    docs.append(
        EndpointDoc(
            operation_key="data.graphql",
            service="data",
            method="POST",
            path="/graphql",
            summary="Query the Data API graph",
            semantic_kind="graphql",
            semantic_summary=(
                "Use the archive metadata graph when you want field-selective retrieval or "
                "cross-object "
                "navigation without multiple REST round-trips."
            ),
            source_url=SERVICE_SOURCES["data"],
            request_body_required=True,
            request_body_content_types=("application/json",),
            response_content_types=("application/json",),
            notes=(
                "The GraphQL schema is broader than the REST surface and supports archive-wide "
                "traversals.",
                "Common roots include entry, entries, polymer_entity, polymer_entities, and "
                "chem_comp.",
            ),
        )
    )
    return docs


def _data_rest_doc(operation_key: str, path: str) -> EndpointDoc:
    path_params = tuple(
        ParameterDoc(
            name=name,
            location="path",
            required=True,
            description=_path_parameter_description(name),
            schema_type="string",
        )
        for name in re.findall(r"{([^}]+)}", path)
    )
    semantic_kind, summary, semantic_summary = _data_semantics(path)
    return EndpointDoc(
        operation_key=operation_key,
        service="data",
        method="GET",
        path=f"/rest/v1{path}",
        summary=summary,
        semantic_kind=semantic_kind,
        semantic_summary=semantic_summary,
        source_url="https://data.rcsb.org/redoc/index.html",
        path_parameters=path_params,
        response_content_types=("application/json",),
    )


def _data_semantics(path: str) -> tuple[str, str, str]:
    if path.startswith("/core/entry/"):
        return (
            "entry",
            "Fetch entry-level structure metadata",
            "Top-level structure record for a PDB entry or supported computed model.",
        )
    if path.startswith("/core/polymer_entity/"):
        return (
            "polymer_entity",
            "Fetch a polymer entity within an entry",
            "Unique macromolecular molecule definition inside an entry, independent of chain "
            "copies.",
        )
    if path.startswith("/core/polymer_entity_instance/"):
        return (
            "polymer_instance",
            "Fetch a polymer chain instance within an entry",
            "Chain-level view of a polymer entity as realized in the deposited coordinates.",
        )
    if path.startswith("/core/nonpolymer_entity_instance/"):
        return (
            "nonpolymer_instance",
            "Fetch a non-polymer instance within an entry",
            "Specific ligand or small-molecule instance as placed in the structure.",
        )
    if path.startswith("/core/nonpolymer_entity/"):
        return (
            "nonpolymer_entity",
            "Fetch a non-polymer entity within an entry",
            "Unique ligand or other non-polymer chemical component occurring in the entry.",
        )
    if path.startswith("/core/branched_entity_instance/"):
        return (
            "branched_instance",
            "Fetch a branched entity instance within an entry",
            "Specific branched carbohydrate or glycan instance in the coordinates.",
        )
    if path.startswith("/core/branched_entity/"):
        return (
            "branched_entity",
            "Fetch a branched entity within an entry",
            "Unique branched carbohydrate or glycan definition inside the entry.",
        )
    if path.startswith("/core/assembly/"):
        return (
            "assembly",
            "Fetch a biological assembly",
            "Quaternary structure-level representation of the deposited entry.",
        )
    if path.startswith("/core/interface/"):
        return (
            "interface",
            "Fetch a polymer interface",
            "Pairwise polymeric interface metadata inside a specific biological assembly.",
        )
    if path.startswith("/core/chemcomp/"):
        return (
            "chemical_component",
            "Fetch a chemical component dictionary record",
            "Dictionary-level ligand or monomer definition, independent of any particular entry.",
        )
    if path.startswith("/core/drugbank/"):
        return (
            "drug_annotation",
            "Fetch DrugBank annotations for a chemical component",
            "External pharmacological annotations mapped onto a chemical component identifier.",
        )
    if path.startswith("/core/pubmed/"):
        return (
            "citation",
            "Fetch citation annotations for an entry",
            "Publication-centric metadata associated with the structure entry.",
        )
    if path.startswith("/core/uniprot/"):
        return (
            "cross_reference",
            "Fetch UniProt annotations for a polymer entity",
            "Sequence-centric annotations and mappings between an entry polymer entity and "
            "UniProt.",
        )
    if path.startswith("/core/entry_groups/"):
        return (
            "group",
            "Fetch an entry group",
            "Aggregated cluster or grouping metadata over entries.",
        )
    if path.startswith("/core/group_provenance/"):
        return (
            "group_provenance",
            "Fetch group provenance metadata",
            "Explains how a grouping or clustering set was produced and versioned.",
        )
    if path.startswith("/core/polymer_entity_groups/"):
        return (
            "group",
            "Fetch a polymer entity group",
            "Cluster-level metadata over polymer entities rather than entries.",
        )
    if path.startswith("/core/nonpolymer_entity_groups/"):
        return (
            "group",
            "Fetch a non-polymer entity group",
            "Cluster-level metadata over ligands and other non-polymer entities.",
        )
    if path.startswith("/holdings/current/"):
        return (
            "repository_holding",
            "Fetch current repository holdings",
            "Registry-style lists of currently released identifiers in the archive.",
        )
    if path.startswith("/holdings/removed/entry_ids"):
        return (
            "repository_holding",
            "Fetch removed entry identifiers",
            "List entries that were removed from the public archive.",
        )
    if path.startswith("/holdings/removed/"):
        return (
            "repository_holding",
            "Fetch removed-entry metadata",
            "Removal metadata for a specific entry identifier.",
        )
    if path.startswith("/holdings/status/"):
        return (
            "repository_holding",
            "Fetch release status for a specific entry",
            "Single-entry status lookup for whether the entry is current, removed, or unreleased.",
        )
    if path == "/holdings/status":
        return (
            "repository_holding",
            "Fetch release status overview",
            "Archive-wide status summary surface for release-state information.",
        )
    if path.startswith("/holdings/unreleased/entry_ids"):
        return (
            "repository_holding",
            "Fetch unreleased entry identifiers",
            "List unreleased identifiers currently tracked by the repository.",
        )
    if path.startswith("/holdings/unreleased/"):
        return (
            "repository_holding",
            "Fetch unreleased-entry metadata",
            "Metadata for a specific unreleased entry identifier.",
        )
    if path.startswith("/holdings/unreleased"):
        return (
            "repository_holding",
            "Fetch unreleased holdings",
            "Archive-wide unreleased holdings surface.",
        )
    if path.startswith("/schema/"):
        schema_name = path.split("/")[-1]
        return (
            "schema",
            f"Fetch the JSON schema for {schema_name}",
            "Machine-readable schema for validating or understanding the corresponding Data API "
            "payload.",
        )
    raise ValueError(f"unhandled data path: {path}")


def _build_search_docs() -> list[EndpointDoc]:
    common_summary = (
        "Run an archive-wide search query over structures, assemblies, polymer entities, or other "
        "supported return types."
    )
    params = (
        ParameterDoc(
            name="json",
            location="query",
            required=True,
            description="URL-encoded search request document.",
            schema_type="string",
        ),
    )
    return [
        EndpointDoc(
            operation_key="search.query-get",
            service="search",
            method="GET",
            path="/rcsbsearch/v2/query",
            summary="Run a search query via URL-encoded JSON",
            semantic_kind="search",
            semantic_summary=common_summary,
            source_url=SERVICE_SOURCES["search"],
            query_parameters=params,
            response_content_types=("application/json",),
            notes=(
                "GET is mainly useful for reproducible links and small queries.",
                "The request model supports full-text, attribute, sequence, structure, "
                "grouping, and facets.",
            ),
        ),
        EndpointDoc(
            operation_key="search.query-post",
            service="search",
            method="POST",
            path="/rcsbsearch/v2/query",
            summary="Run a search query via JSON request body",
            semantic_kind="search",
            semantic_summary=common_summary,
            source_url=SERVICE_SOURCES["search"],
            request_body_required=True,
            request_body_content_types=("application/json",),
            response_content_types=("application/json",),
            notes=(
                "POST is the practical default for complex DSL payloads.",
                "Responses can include hits, counts, facets, grouping, and ranking metadata.",
            ),
        ),
    ]


def _build_model_docs() -> list[EndpointDoc]:
    config_params = (
        ParameterDoc("id", "path", True, "Entry identifier such as a PDB ID.", "string"),
        ParameterDoc("encoding", "query", False, "Output encoding.", "string"),
        ParameterDoc("model_nums", "query", False, "Restrict to specific model numbers.", "string"),
    )
    operations: list[EndpointDoc] = []
    model_specs = [
        (
            "model.assembly",
            ("GET", "POST"),
            "/v1/{id}/assembly",
            "assembly_subset",
            "Return a structural assembly subset.",
        ),
        (
            "model.atoms",
            ("GET", "POST"),
            "/v1/{id}/atoms",
            "atom_subset",
            "Return atoms matching coordinate-selection criteria.",
        ),
        (
            "model.full",
            ("GET", "POST"),
            "/v1/{id}/full",
            "full_model",
            "Return the full coordinate model.",
        ),
        (
            "model.ligand",
            ("GET", "POST"),
            "/v1/{id}/ligand",
            "ligand_subset",
            "Return a ligand-focused coordinate subset.",
        ),
        (
            "model.residue-interaction",
            ("GET", "POST"),
            "/v1/{id}/residueInteraction",
            "interaction_subset",
            "Return residues interacting with a residue selection.",
        ),
        (
            "model.residue-surroundings",
            ("GET", "POST"),
            "/v1/{id}/residueSurroundings",
            "spatial_subset",
            "Return atoms or residues in the spatial neighborhood of a residue selection.",
        ),
        (
            "model.surrounding-ligands",
            ("GET", "POST"),
            "/v1/{id}/surroundingLigands",
            "spatial_subset",
            "Identify complete ligands near a selected atom set.",
        ),
        (
            "model.symmetry-mates",
            ("GET", "POST"),
            "/v1/{id}/symmetryMates",
            "symmetry_subset",
            "Compute crystal symmetry mates around the requested region.",
        ),
        (
            "model.query-many",
            ("GET", "POST"),
            "/v1/query-many",
            "batch_query",
            "Execute multiple ModelServer subset queries in one call.",
        ),
    ]
    for operation_key, methods, path, semantic_kind, semantic_summary in model_specs:
        for method in methods:
            operation_key_with_method = (
                operation_key if method == "GET" else f"{operation_key}-post"
            )
            operations.append(
                EndpointDoc(
                    operation_key=operation_key_with_method,
                    service="model",
                    method=method,
                    path=path,
                    summary=semantic_summary.rstrip("."),
                    semantic_kind=semantic_kind,
                    semantic_summary=semantic_summary,
                    source_url=SERVICE_SOURCES["model"],
                    path_parameters=() if "{id}" not in path else (config_params[0],),
                    query_parameters=()
                    if operation_key == "model.query-many"
                    else config_params[1:],
                    request_body_required=method == "POST",
                    request_body_content_types=("application/json",) if method == "POST" else (),
                    response_content_types=("text/plain", "application/octet-stream"),
                    notes=(
                        "ModelServer is about coordinates and structural subsets, not entry "
                        "metadata.",
                        "Binary CIF (`bcif`) is the compact default for programmatic consumption.",
                    ),
                )
            )
    return operations


def _build_volume_docs() -> list[EndpointDoc]:
    source_param = ParameterDoc(
        "source",
        "path",
        True,
        "Volumetric source family. Official docs list `x-ray` and `em`.",
        "string",
    )
    id_param = ParameterDoc(
        "id",
        "path",
        True,
        "PDB ID for x-ray maps or EMDB ID such as `emd-8116` for EM maps.",
        "string",
    )
    return [
        EndpointDoc(
            operation_key="volume.info",
            service="volume",
            method="GET",
            path="/{source}/{id}/",
            summary="Fetch volume availability and bounding metadata",
            semantic_kind="volume_info",
            semantic_summary=(
                "Probe whether a map exists and inspect the maximum queryable region before "
                "retrieving "
                "density."
            ),
            source_url=SERVICE_SOURCES["volume"],
            path_parameters=(source_param, id_param),
            response_content_types=("application/json",),
        ),
        EndpointDoc(
            operation_key="volume.box",
            service="volume",
            method="GET",
            path="/{source}/{id}/box/{a1,a2,a3}/{b1,b2,b3}/",
            summary="Fetch density in a bounded box",
            semantic_kind="volume_subset",
            semantic_summary=(
                "Return density values for a spatial box. Use this when a full map would be too "
                "large."
            ),
            source_url=SERVICE_SOURCES["volume"],
            path_parameters=(
                source_param,
                id_param,
                ParameterDoc("a1,a2,a3", "path", True, "Bottom-left box corner triple.", "list"),
                ParameterDoc("b1,b2,b3", "path", True, "Top-right box corner triple.", "list"),
            ),
            query_parameters=(
                ParameterDoc(
                    "encoding", "query", False, "Volume encoding (`cif` or `bcif`).", "string"
                ),
                ParameterDoc(
                    "detail",
                    "query",
                    False,
                    "Detail level controlling returned voxel count.",
                    "integer",
                ),
                ParameterDoc(
                    "space", "query", False, "Coordinate frame: cartesian or fractional.", "string"
                ),
            ),
            response_content_types=("text/plain", "application/octet-stream"),
        ),
        EndpointDoc(
            operation_key="volume.cell",
            service="volume",
            method="GET",
            path="/{source}/{id}/cell/",
            summary="Fetch the full downsampled map cell",
            semantic_kind="volume_cell",
            semantic_summary=(
                "Return the whole unit cell or full EM map at an appropriate downsampled "
                "resolution."
            ),
            source_url=SERVICE_SOURCES["volume"],
            path_parameters=(source_param, id_param),
            query_parameters=(
                ParameterDoc(
                    "encoding", "query", False, "Volume encoding (`cif` or `bcif`).", "string"
                ),
                ParameterDoc(
                    "detail",
                    "query",
                    False,
                    "Detail level controlling returned voxel count.",
                    "integer",
                ),
            ),
            response_content_types=("text/plain", "application/octet-stream"),
        ),
    ]


def _build_sequence_docs() -> list[EndpointDoc]:
    return [
        EndpointDoc(
            operation_key="sequence.graphql",
            service="sequence",
            method="POST",
            path="/graphql",
            summary="Query sequence alignments and positional annotations",
            semantic_kind="graphql",
            semantic_summary=(
                "GraphQL surface for moving between structure coordinates and reference sequences "
                "or "
                "annotation tracks."
            ),
            source_url=SERVICE_SOURCES["sequence"],
            request_body_required=True,
            request_body_content_types=("application/json",),
            response_content_types=("application/json",),
            notes=(
                "The documented root fields are `alignment` and `annotations`.",
                "Use this API when the Data API tells you what the structure is, but you need "
                "residue-level sequence mappings.",
            ),
        )
    ]


def _build_alignment_docs() -> list[EndpointDoc]:
    submit_query = (
        ParameterDoc(
            "json", "query", True, "URL-encoded alignment job request document.", "string"
        ),
    )
    results_query = (
        ParameterDoc("uuid", "query", True, "Alignment job ticket returned by submit.", "string"),
    )
    notes = (
        "The public docs compute the base endpoint as `https://alignment.rcsb.org/structures`.",
        "Results are asynchronous: submit first, then poll `results` with the returned job UUID.",
    )
    return [
        EndpointDoc(
            operation_key="alignment.submit-get",
            service="alignment",
            method="GET",
            path="/submit",
            summary="Submit a structure alignment job via URL-encoded JSON",
            semantic_kind="job_submission",
            semantic_summary="Start an asynchronous pairwise structure alignment computation.",
            source_url=SERVICE_SOURCES["alignment"],
            query_parameters=submit_query,
            response_content_types=("application/json",),
            notes=notes,
        ),
        EndpointDoc(
            operation_key="alignment.submit-post",
            service="alignment",
            method="POST",
            path="/submit",
            summary="Submit a structure alignment job via JSON request body",
            semantic_kind="job_submission",
            semantic_summary="Start an asynchronous pairwise structure alignment computation.",
            source_url=SERVICE_SOURCES["alignment"],
            request_body_required=True,
            request_body_content_types=("application/json", "multipart/form-data"),
            response_content_types=("application/json",),
            notes=notes,
        ),
        EndpointDoc(
            operation_key="alignment.results",
            service="alignment",
            method="GET",
            path="/results",
            summary="Poll alignment job status or retrieve completed results",
            semantic_kind="job_results",
            semantic_summary=(
                "Check whether an alignment job is still running, failed, or completed, and "
                "obtain the "
                "result payload."
            ),
            source_url=SERVICE_SOURCES["alignment"],
            query_parameters=results_query,
            response_content_types=("application/json",),
            notes=notes,
        ),
    ]


def _path_parameter_description(name: str) -> str:
    descriptions = {
        "entry_id": "RCSB entry identifier such as `4HHB`.",
        "assembly_id": "Assembly identifier within an entry.",
        "entity_id": "Entity identifier within an entry.",
        "asym_id": "Asymmetric-unit or chain identifier within an entry.",
        "interface_id": "Interface identifier within an assembly.",
        "comp_id": "Chemical component dictionary identifier.",
        "group_id": "Group or cluster identifier.",
        "group_provenance_id": "Group provenance identifier.",
    }
    return descriptions.get(name, f"Path parameter `{name}`.")
