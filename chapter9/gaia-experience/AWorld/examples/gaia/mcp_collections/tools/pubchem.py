"""
PubChem MCP Server

This module provides MCP server functionality for accessing PubChem database programmatically.
It supports compound searches, property retrieval, and structure-based queries using PubChem's REST API.

Key features:
- Compound search by name, CID, SMILES, or InChI
- Property retrieval (molecular weight, formula, etc.)
- Structure similarity searches
- Bioactivity data access
- 3D structure downloads
- Rate limiting compliance (max 5 requests/second)

Main functions:
- mcp_search_compounds: Search for compounds by various identifiers
- mcp_get_compound_properties: Retrieve compound properties
- mcp_get_compound_synonyms: Get compound names and synonyms
- mcp_search_similar_compounds: Find structurally similar compounds
- mcp_get_bioactivity_data: Retrieve bioactivity assay data
- mcp_download_structure: Download 2D/3D structure files
"""

import time
import traceback
from datetime import datetime
from typing import Literal
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from aworld.logs.util import Color
from examples.gaia.mcp_collections.base import ActionArguments, ActionCollection, ActionResponse


# pylint: disable=C0301
class CompoundData(BaseModel):
    """Structured compound data from PubChem."""

    cid: int | None = None
    name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    smiles: str | None = None
    inchi: str | None = None
    synonyms: list[str] = []


class PubChemMetadata(BaseModel):
    """Metadata for PubChem operation results."""

    query_type: str
    query_value: str
    api_endpoint: str
    response_time: float
    total_results: int | None = None
    rate_limit_delay: float | None = None
    error_type: str | None = None
    timestamp: str


class PubChemCollection(ActionCollection):
    """MCP service for PubChem database access with comprehensive chemical data retrieval.

    Provides access to PubChem's extensive chemical database including:
    - Compound identification and search capabilities
    - Chemical property and structure data
    - Bioactivity and assay information
    - Structure similarity searches
    - 2D/3D molecular structure downloads
    - Synonym and nomenclature data

    Complies with PubChem usage policies:
    - Maximum 5 requests per second
    - Automatic rate limiting
    - Proper error handling for timeouts
    """

    def __init__(self, arguments: ActionArguments) -> None:
        super().__init__(arguments)

        # PubChem API configuration
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.base_url_view = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"
        self.request_delay = 0.2  # 200ms delay to stay under 5 req/sec limit
        self.last_request_time = 0.0

        # Request timeout settings
        self.timeout = 30  # PubChem's 30-second limit

        # Initialize request session with headers
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "AWorld-PubChem-MCP/1.0 (https://github.com/aworld-framework)", "Accept": "application/json"}
        )

        self._color_log("PubChem MCP Service initialized", Color.green, "debug")
        self._color_log(f"Base URL: {self.base_url}", Color.blue, "debug")

    def _rate_limit(self) -> float:
        """Enforce rate limiting to comply with PubChem usage policy.

        Returns:
            Actual delay time applied
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_delay:
            delay = self.request_delay - time_since_last
            time.sleep(delay)
            self.last_request_time = time.time()
            return delay

        self.last_request_time = current_time
        return 0.0

    def _make_request(self, url: str, params: dict = None) -> tuple[dict | None, float]:
        """Make a rate-limited request to PubChem API.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            Tuple of (response_data, response_time)

        Raises:
            requests.RequestException: For API request failures
        """
        start_time = time.time()

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return response.json(), response_time
            elif response.status_code == 503:
                raise requests.RequestException("PubChem service temporarily unavailable (503)")
            else:
                raise requests.RequestException(f"HTTP {response.status_code}: {response.text}")

        except requests.Timeout as e:
            response_time = time.time() - start_time
            raise requests.RequestException(f"Request timeout after {self.timeout}s") from e
        except requests.RequestException:
            response_time = time.time() - start_time
            raise

    def mcp_search_compounds(
        self,
        query: str = Field(description="Search query (compound name, CID, SMILES, InChI, etc.)"),
        search_type: Literal["name", "cid", "smiles", "inchi", "formula"] = Field(
            default="name",
            description="Type of search: name (compound name), cid (PubChem ID), smiles, inchi, or formula",
        ),
        max_results: int = Field(default=10, description="Maximum number of results to return (1-100)", ge=1, le=100),
    ) -> ActionResponse:
        """Search for chemical compounds in PubChem database.

        Supports multiple search types:
        - Name: Search by common or IUPAC names
        - CID: Search by PubChem Compound ID
        - SMILES: Search by SMILES notation
        - InChI: Search by InChI identifier
        - Formula: Search by molecular formula

        Args:
            query: Search term or identifier
            search_type: Type of search to perform
            max_results: Maximum number of compounds to return

        Returns:
            ActionResponse with compound search results and metadata
        """
        try:
            # Handle FieldInfo objects
            if isinstance(query, FieldInfo):
                query = query.default
            if isinstance(search_type, FieldInfo):
                search_type = search_type.default
            if isinstance(max_results, FieldInfo):
                max_results = max_results.default

            if not query or not query.strip():
                raise ValueError("Search query is required")

            self._color_log(f"Searching PubChem for: {query} (type: {search_type})", Color.cyan)

            # Build API URL based on search type
            if search_type == "cid":
                url = f"{self.base_url}/compound/cid/{quote(str(query))}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
            elif search_type == "name":
                url = f"{self.base_url}/compound/name/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
            elif search_type == "smiles":
                url = f"{self.base_url}/compound/smiles/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
            elif search_type == "inchi":
                url = f"{self.base_url}/compound/inchi/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
            elif search_type == "formula":
                url = f"{self.base_url}/compound/formula/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
            else:
                raise ValueError(f"Unsupported search type: {search_type}")

            # Make API request
            data, response_time = self._make_request(url)

            # Parse results
            compounds = []
            if data and "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                properties_list = data["PropertyTable"]["Properties"][:max_results]

                for prop in properties_list:
                    compound = CompoundData(
                        cid=prop.get("CID"),
                        name=prop.get("Title"),
                        molecular_formula=prop.get("MolecularFormula"),
                        molecular_weight=prop.get("MolecularWeight"),
                        smiles=prop.get("CanonicalSMILES"),
                        inchi=prop.get("InChI"),
                    )
                    compounds.append(compound)

            # Format results for LLM
            if compounds:
                result_lines = [f"Found {len(compounds)} compound(s) for query '{query}':\n"]

                for i, compound in enumerate(compounds, 1):
                    result_lines.append(f"{i}. **{compound.name}** (CID: {compound.cid})")
                    result_lines.append(f"   - Formula: {compound.molecular_formula}")
                    result_lines.append(f"   - Molecular Weight: {compound.molecular_weight} g/mol")
                    result_lines.append(f"   - SMILES: {compound.smiles}")
                    if compound.inchi:
                        result_lines.append(
                            f"   - InChI: {compound.inchi[:100]}..."
                            if len(compound.inchi) > 100
                            else f"   - InChI: {compound.inchi}"
                        )
                    result_lines.append("")

                message = "\n".join(result_lines)
            else:
                message = f"No compounds found for query '{query}' using search type '{search_type}'"

            # Prepare metadata
            metadata = PubChemMetadata(
                query_type=search_type,
                query_value=query,
                api_endpoint=url,
                response_time=response_time,
                total_results=len(compounds),
                timestamp=datetime.now().isoformat(),
            )

            self._color_log(f"Found {len(compounds)} compounds ({response_time:.2f}s)", Color.green)

            return ActionResponse(success=True, message=message, metadata=metadata.model_dump())

        except ValueError as e:
            self.logger.error(f"Invalid input: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"Invalid input: {str(e)}",
                metadata={"error_type": "invalid_input", "error_message": str(e)},
            )
        except requests.RequestException as e:
            self.logger.error(f"PubChem API error: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"PubChem API error: {str(e)}",
                metadata={"error_type": "api_error", "error_message": str(e)},
            )
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}: {traceback.format_exc()}")
            return ActionResponse(
                success=False,
                message=f"Search failed: {str(e)}",
                metadata={"error_type": "general_error", "error_message": str(e)},
            )

    def mcp_get_compound_synonyms(
        self,
        cid: int = Field(description="PubChem Compound ID (CID)"),
        max_synonyms: int = Field(default=20, description="Maximum number of synonyms to return (1-100)", ge=1, le=100),
    ) -> ActionResponse:
        """Retrieve synonyms and alternative names for a PubChem compound.

        Args:
            cid: PubChem Compound ID
            max_synonyms: Maximum number of synonyms to return

        Returns:
            ActionResponse with compound synonyms and metadata
        """
        try:
            # Handle FieldInfo objects
            if isinstance(cid, FieldInfo):
                cid = cid.default
            if isinstance(max_synonyms, FieldInfo):
                max_synonyms = max_synonyms.default

            if not cid or cid <= 0:
                raise ValueError("Valid PubChem CID is required")

            self._color_log(f"Retrieving synonyms for CID: {cid}", Color.cyan)

            # Build API URL for synonyms
            url = f"{self.base_url}/compound/cid/{cid}/synonyms/JSON"

            # Make API request
            data, response_time = self._make_request(url)

            # Parse synonyms
            synonyms = []
            if data and "InformationList" in data and "Information" in data["InformationList"]:
                info_list = data["InformationList"]["Information"]
                if info_list and "Synonym" in info_list[0]:
                    synonyms = info_list[0]["Synonym"][:max_synonyms]

            # Format results for LLM
            if synonyms:
                result_lines = [f"Found {len(synonyms)} synonym(s) for CID {cid}:\n"]

                for i, synonym in enumerate(synonyms, 1):
                    result_lines.append(f"{i}. {synonym}")

                message = "\n".join(result_lines)
            else:
                message = f"No synonyms found for CID {cid}"

            # Prepare metadata
            metadata = PubChemMetadata(
                query_type="synonyms",
                query_value=str(cid),
                api_endpoint=url,
                response_time=response_time,
                total_results=len(synonyms),
                timestamp=datetime.now().isoformat(),
            )

            self._color_log(f"Retrieved {len(synonyms)} synonyms ({response_time:.2f}s)", Color.green)

            return ActionResponse(success=True, message=message, metadata=metadata.model_dump())

        except ValueError as e:
            self.logger.error(f"Invalid input: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"Invalid input: {str(e)}",
                metadata={"error_type": "invalid_input", "error_message": str(e)},
            )
        except requests.RequestException as e:
            self.logger.error(f"PubChem API error: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"PubChem API error: {str(e)}",
                metadata={"error_type": "api_error", "error_message": str(e)},
            )
        except Exception as e:
            self.logger.error(f"Synonym retrieval failed: {str(e)}: {traceback.format_exc()}")
            return ActionResponse(
                success=False,
                message=f"Synonym retrieval failed: {str(e)}",
                metadata={"error_type": "general_error", "error_message": str(e)},
            )

    def mcp_get_compound_properties(
        self,
        cid: int = Field(description="PubChem Compound ID (CID)"),
        properties: list[str] = Field(
            default=[
                "MolecularWeight",
                "MolecularFormula",
                "CanonicalSMILES",
                "InChI",
                "XLogP",
                "TPSA",
                "HBondDonorCount",
                "HBondAcceptorCount",
            ],
            description="List of properties to retrieve (e.g., MolecularWeight, XLogP, TPSA)",
        ),
    ) -> ActionResponse:
        """Retrieve detailed chemical properties for a PubChem compound.

        Common properties include:
        - MolecularWeight: Molecular weight in g/mol
        - MolecularFormula: Chemical formula
        - CanonicalSMILES: SMILES notation
        - InChI: InChI identifier
        - XLogP: Partition coefficient
        - TPSA: Topological polar surface area
        - HBondDonorCount: Hydrogen bond donor count
        - HBondAcceptorCount: Hydrogen bond acceptor count

        Args:
            cid: PubChem Compound ID
            properties: List of property names to retrieve

        Returns:
            ActionResponse with compound properties and metadata
        """
        try:
            # Handle FieldInfo objects
            if isinstance(cid, FieldInfo):
                cid = cid.default
            if isinstance(properties, FieldInfo):
                properties = properties.default

            if not cid or cid <= 0:
                raise ValueError("Valid PubChem CID is required")

            if not properties:
                properties = ["MolecularWeight", "MolecularFormula", "CanonicalSMILES"]

            self._color_log(f"Retrieving properties for CID: {cid}", Color.cyan)

            # Build API URL for properties
            props_str = ",".join(properties)
            url = f"{self.base_url}/compound/cid/{cid}/property/{props_str}/JSON"

            # Make API request
            data, response_time = self._make_request(url)

            # Parse properties
            compound_props = {}
            if data and "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                props_data = data["PropertyTable"]["Properties"][0]
                compound_props = {k: v for k, v in props_data.items() if k != "CID"}

            # Format results for LLM
            if compound_props:
                result_lines = [f"Properties for PubChem CID {cid}:\n"]

                for prop_name, prop_value in compound_props.items():
                    if prop_name == "InChI" and isinstance(prop_value, str) and len(prop_value) > 100:
                        result_lines.append(f"**{prop_name}**: {prop_value[:100]}...")
                    else:
                        result_lines.append(f"**{prop_name}**: {prop_value}")

                message = "\n".join(result_lines)
            else:
                message = f"No properties found for CID {cid}"

            # Prepare metadata
            metadata = PubChemMetadata(
                query_type="properties",
                query_value=str(cid),
                api_endpoint=url,
                response_time=response_time,
                total_results=len(compound_props),
                timestamp=datetime.now().isoformat(),
            )

            self._color_log(f"Retrieved {len(compound_props)} properties ({response_time:.2f}s)", Color.green)

            return ActionResponse(success=True, message=message, metadata=metadata.model_dump())

        except ValueError as e:
            self.logger.error(f"Invalid input: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"Invalid input: {str(e)}",
                metadata={"error_type": "invalid_input", "error_message": str(e)},
            )
        except requests.RequestException as e:
            self.logger.error(f"PubChem API error: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"PubChem API error: {str(e)}",
                metadata={"error_type": "api_error", "error_message": str(e)},
            )
        except Exception as e:
            self.logger.error(f"Property retrieval failed: {str(e)}: {traceback.format_exc()}")
            return ActionResponse(
                success=False,
                message=f"Property retrieval failed: {str(e)}",
                metadata={"error_type": "general_error", "error_message": str(e)},
            )

    def mcp_search_similar_compounds(
        self,
        cid: int = Field(description="PubChem Compound ID to find similar compounds for"),
        similarity_threshold: float = Field(
            default=0.9, description="Similarity threshold (0.0-1.0, higher = more similar)", ge=0.0, le=1.0
        ),
        max_results: int = Field(
            default=10, description="Maximum number of similar compounds to return (1-50)", ge=1, le=50
        ),
    ) -> ActionResponse:
        """Find structurally similar compounds using PubChem's similarity search.

        Uses Tanimoto similarity coefficient for 2D structure comparison.

        Args:
            cid: Reference compound CID for similarity search
            similarity_threshold: Minimum similarity score (0.0-1.0)
            max_results: Maximum number of similar compounds to return

        Returns:
            ActionResponse with similar compounds and metadata
        """
        try:
            # Handle FieldInfo objects
            if isinstance(cid, FieldInfo):
                cid = cid.default
            if isinstance(similarity_threshold, FieldInfo):
                similarity_threshold = similarity_threshold.default
            if isinstance(max_results, FieldInfo):
                max_results = max_results.default

            if not cid or cid <= 0:
                raise ValueError("Valid PubChem CID is required")

            self._color_log(f"Searching for compounds similar to CID: {cid}", Color.cyan)

            # Build API URL for similarity search
            threshold_percent = int(similarity_threshold * 100)
            url = f"{self.base_url}/compound/fastsimilarity_2d/cid/{cid}/property/Title,MolecularFormula,MolecularWeight/JSON"
            params = {"Threshold": threshold_percent, "MaxRecords": max_results}

            # Make API request
            data, response_time = self._make_request(url, params)

            # Parse similar compounds
            similar_compounds: list[CompoundData] = []
            if data and "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                properties_list = data["PropertyTable"]["Properties"]

                for prop in properties_list:
                    if prop.get("CID") != cid:  # Exclude the query compound itself
                        compound = CompoundData(
                            cid=prop.get("CID"),
                            name=prop.get("Title"),
                            molecular_formula=prop.get("MolecularFormula"),
                            molecular_weight=prop.get("MolecularWeight"),
                        )
                        similar_compounds.append(compound)

            # Format results for LLM
            if similar_compounds:
                result_lines = [
                    f"Found {len(similar_compounds)} compound(s) similar to CID {cid} (threshold: {similarity_threshold}):\n"
                ]

                for i, compound in enumerate(similar_compounds, 1):
                    result_lines.append(f"{i}. **{compound.name}** (CID: {compound.cid})")
                    result_lines.append(f"   - Formula: {compound.molecular_formula}")
                    result_lines.append(f"   - Molecular Weight: {compound.molecular_weight} g/mol")
                    result_lines.append("")

                message = "\n".join(result_lines)
            else:
                message = f"No similar compounds found for CID {cid} with similarity threshold {similarity_threshold}"

            # Prepare metadata
            metadata = PubChemMetadata(
                query_type="similarity",
                query_value=str(cid),
                api_endpoint=url,
                response_time=response_time,
                total_results=len(similar_compounds),
                timestamp=datetime.now().isoformat(),
            )

            self._color_log(f"Found {len(similar_compounds)} similar compounds ({response_time:.2f}s)", Color.green)

            return ActionResponse(success=True, message=message, metadata=metadata.model_dump())

        except ValueError as e:
            self.logger.error(f"Invalid input: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"Invalid input: {str(e)}",
                metadata={"error_type": "invalid_input", "error_message": str(e)},
            )
        except requests.RequestException as e:
            self.logger.error(f"PubChem API error: {str(e)}")
            return ActionResponse(
                success=False,
                message=f"PubChem API error: {str(e)}",
                metadata={"error_type": "api_error", "error_message": str(e)},
            )
        except Exception as e:
            self.logger.error(f"Similarity search failed: {str(e)}: {traceback.format_exc()}")
            return ActionResponse(
                success=False,
                message=f"Similarity search failed: {str(e)}",
                metadata={"error_type": "general_error", "error_message": str(e)},
            )

    def mcp_get_pubchem_capabilities(self) -> ActionResponse:
        """Get information about the PubChem service capabilities.

        Returns:
            ActionResponse with service capabilities and configuration
        """
        capabilities = {
            "Compound Search": "Search by name, CID, SMILES, InChI, or molecular formula",
            "Property Retrieval": "Get molecular weight, formula, SMILES, physicochemical properties",
            "Synonym Lookup": "Retrieve alternative names and identifiers for compounds",
            "Similarity Search": "Find structurally similar compounds using Tanimoto similarity",
            "Rate Limiting": "Compliant with PubChem's 5 requests/second limit",
            "Data Formats": "JSON responses with structured compound data",
        }

        capability_list = "\n".join(
            [f"**{capability}**: {description}" for capability, description in capabilities.items()]
        )

        metadata = {
            "base_url": self.base_url,
            "rate_limit": "5 requests/second",
            "timeout": f"{self.timeout} seconds",
            "supported_capabilities": list(capabilities.keys()),
            "total_capabilities": len(capabilities),
            "search_types": ["name", "cid", "smiles", "inchi", "formula"],
            "data_source": "PubChem (NCBI)",
        }

        return ActionResponse(
            success=True, message=f"PubChem MCP Service Capabilities:\n\n{capability_list}", metadata=metadata
        )


# Example usage and entry point
if __name__ == "__main__":
    load_dotenv()

    # Default arguments for testing
    args = ActionArguments(name="pubchem_service", transport="stdio", workspace="~")

    # Initialize and run the PubChem service
    try:
        service = PubChemCollection(args)
        service.run()
    except Exception as e:
        print(f"An error occurred: {e}: {traceback.format_exc()}")
