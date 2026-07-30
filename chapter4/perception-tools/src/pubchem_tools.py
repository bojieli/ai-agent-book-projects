"""
PubChem chemical compound data tools.
Based on AWorld MCP server implementation.
"""
import json
import logging
import time
import traceback
from typing import Union, Literal
from urllib.parse import quote, urlsplit, urlunsplit

import requests
from dotenv import load_dotenv
from mcp.types import TextContent
from pydantic import BaseModel, Field

from base import ActionResponse


load_dotenv()


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


class PubChemClient:
    """PubChem API client with rate limiting."""
    
    def __init__(self):
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.request_delay = 0.2  # 200ms delay to stay under 5 req/sec limit
        self.last_request_time = 0.0
        self.timeout = 30
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PerceptionToolsMCP/1.0",
            "Accept": "application/json"
        })
    
    def _rate_limit(self) -> float:
        """Enforce rate limiting to comply with PubChem usage policy."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            delay = self.request_delay - time_since_last
            time.sleep(delay)
            self.last_request_time = time.time()
            return delay
        
        self.last_request_time = current_time
        return 0.0
    
    @staticmethod
    def _listkey_poll_url(url: str, list_key: str) -> str:
        """Convert an asynchronous PUG REST request into its ListKey poll URL."""
        parsed = urlsplit(url)
        compound_marker = "/compound/"
        compound_index = parsed.path.find(compound_marker)
        if compound_index < 0:
            raise requests.RequestException("PubChem ListKey response for an unsupported endpoint")

        operation_start = compound_index + len(compound_marker)
        operation_indexes = [
            index
            for marker in ("/property/", "/cids/", "/synonyms/")
            if (index := parsed.path.find(marker, operation_start)) >= 0
        ]
        if not operation_indexes:
            raise requests.RequestException("PubChem ListKey response did not identify a poll operation")

        operation_index = min(operation_indexes)
        poll_path = (
            parsed.path[:operation_start]
            + f"listkey/{quote(list_key, safe='')}"
            + parsed.path[operation_index:]
        )
        return urlunsplit((parsed.scheme, parsed.netloc, poll_path, parsed.query, parsed.fragment))

    def make_request(
        self,
        url: str,
        params: dict = None,
        max_retries: int = 12,
        _origin_url: str | None = None,
        _started_at: float | None = None,
    ) -> tuple[dict | None, float]:
        """Make a rate-limited request to PubChem API with retry for async operations."""
        origin_url = _origin_url or url
        started_at = _started_at if _started_at is not None else time.perf_counter()
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json(), time.perf_counter() - started_at
            elif response.status_code == 202:
                # PUG REST returns a ListKey for long-running searches. Polling the
                # original URL starts a new job, so switch to the documented
                # list-key endpoint and retain the complete request latency.
                if max_retries > 0:
                    waiting = response.json().get("Waiting", {})
                    list_key = str(waiting.get("ListKey", "")).strip()
                    if not list_key:
                        raise requests.RequestException("PubChem async response omitted ListKey")
                    poll_url = self._listkey_poll_url(url, list_key)
                    logging.info("PubChem async operation, waiting 2s before polling ListKey")
                    time.sleep(2)
                    return self.make_request(
                        poll_url,
                        params,
                        max_retries - 1,
                        _origin_url=origin_url,
                        _started_at=started_at,
                    )
                else:
                    raise requests.RequestException("PubChem async operation timeout after retries")
            elif response.status_code in {429, 500, 502, 503, 504} and max_retries > 0:
                # A ListKey job can fail independently inside PubChem. Start a
                # fresh copy of the original query in that case; otherwise
                # retry the same endpoint. All retries remain bounded.
                retry_url = origin_url if "/listkey/" in url else url
                logging.warning(
                    "PubChem transient HTTP %s; retrying %s",
                    response.status_code,
                    "original query" if retry_url == origin_url else "request",
                )
                time.sleep(2)
                return self.make_request(
                    retry_url,
                    params,
                    max_retries - 1,
                    _origin_url=origin_url,
                    _started_at=started_at,
                )
            else:
                raise requests.RequestException(f"HTTP {response.status_code}: {response.text}")
        
        except requests.Timeout:
            raise requests.RequestException(f"Request timeout after {self.timeout}s")
        except requests.RequestException:
            raise


# Global client instance
_client = None


def get_client() -> PubChemClient:
    """Get or create the global PubChem client."""
    global _client
    if _client is None:
        _client = PubChemClient()
    return _client


async def search_compounds(
    query: str,
    search_type: Literal["name", "cid", "smiles", "inchi", "formula"] = "name",
    max_results: int = 10
) -> Union[str, TextContent]:
    """
    Search for chemical compounds in PubChem database.
    
    Args:
        query: Search term or identifier
        search_type: Type of search (name, cid, smiles, inchi, formula)
        max_results: Maximum number of results (1-100)
        
    Returns:
        TextContent with compound search results
    """
    try:
        if not query or not query.strip():
            raise ValueError("Search query is required")
        
        max_results = max(1, min(max_results, 100))
        
        logging.info(f"🔬 Searching PubChem for: {query} (type: {search_type})")
        
        client = get_client()
        
        # Build API URL based on search type
        if search_type == "cid":
            url = f"{client.base_url}/compound/cid/{quote(str(query))}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
        elif search_type == "name":
            url = f"{client.base_url}/compound/name/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
        elif search_type == "smiles":
            url = f"{client.base_url}/compound/smiles/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
        elif search_type == "inchi":
            url = f"{client.base_url}/compound/inchi/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
        elif search_type == "formula":
            url = f"{client.base_url}/compound/formula/{quote(query)}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,InChI/JSON"
        else:
            raise ValueError(f"Unsupported search type: {search_type}")
        
        # Make API request
        data, response_time = client.make_request(url)
        
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
                    inchi=prop.get("InChI")
                )
                compounds.append(compound)
        
        # Format results
        result = {
            "query": query,
            "search_type": search_type,
            "compounds": [c.model_dump() for c in compounds],
            "count": len(compounds)
        }
        
        metadata = PubChemMetadata(
            query_type=search_type,
            query_value=query,
            api_endpoint=url,
            response_time=response_time,
            total_results=len(compounds)
        )
        
        logging.info(f"✅ Found {len(compounds)} compounds ({response_time:.2f}s)")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata=metadata.model_dump()
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except ValueError as e:
        error_msg = f"Invalid input: {str(e)}"
        logging.error(f"PubChem search error: {error_msg}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "invalid_input"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        logging.error(f"PubChem error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "api_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def get_compound_properties(
    cid: int,
    properties: list[str] | None = None
) -> Union[str, TextContent]:
    """
    Retrieve detailed chemical properties for a PubChem compound.
    
    Args:
        cid: PubChem Compound ID
        properties: List of property names (e.g., MolecularWeight, XLogP)
        
    Returns:
        TextContent with compound properties
    """
    try:
        if not cid or cid <= 0:
            raise ValueError("Valid PubChem CID is required")
        
        if not properties:
            properties = [
                "MolecularWeight", "MolecularFormula", "CanonicalSMILES",
                "InChI", "XLogP", "TPSA", "HBondDonorCount", "HBondAcceptorCount"
            ]
        
        logging.info(f"🔬 Getting properties for CID: {cid}")
        
        client = get_client()
        props_str = ",".join(properties)
        url = f"{client.base_url}/compound/cid/{cid}/property/{props_str}/JSON"
        
        data, response_time = client.make_request(url)
        
        compound_props = {}
        if data and "PropertyTable" in data and "Properties" in data["PropertyTable"]:
            props_data = data["PropertyTable"]["Properties"][0]
            compound_props = {k: v for k, v in props_data.items() if k != "CID"}
        
        result = {
            "cid": cid,
            "properties": compound_props
        }
        
        metadata = PubChemMetadata(
            query_type="properties",
            query_value=str(cid),
            api_endpoint=url,
            response_time=response_time,
            total_results=len(compound_props)
        )
        
        logging.info(f"✅ Retrieved {len(compound_props)} properties")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata=metadata.model_dump()
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Property retrieval failed: {str(e)}"
        logging.error(f"PubChem error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "api_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def get_compound_synonyms(
    cid: int,
    max_synonyms: int = 20
) -> Union[str, TextContent]:
    """
    Retrieve synonyms for a PubChem compound.
    
    Args:
        cid: PubChem Compound ID
        max_synonyms: Maximum number of synonyms (1-100)
        
    Returns:
        TextContent with compound synonyms
    """
    try:
        if not cid or cid <= 0:
            raise ValueError("Valid PubChem CID is required")
        
        max_synonyms = max(1, min(max_synonyms, 100))
        
        logging.info(f"🔬 Getting synonyms for CID: {cid}")
        
        client = get_client()
        url = f"{client.base_url}/compound/cid/{cid}/synonyms/JSON"
        
        data, response_time = client.make_request(url)
        
        synonyms = []
        if data and "InformationList" in data and "Information" in data["InformationList"]:
            info_list = data["InformationList"]["Information"]
            if info_list and "Synonym" in info_list[0]:
                synonyms = info_list[0]["Synonym"][:max_synonyms]
        
        result = {
            "cid": cid,
            "synonyms": synonyms,
            "count": len(synonyms)
        }
        
        metadata = PubChemMetadata(
            query_type="synonyms",
            query_value=str(cid),
            api_endpoint=url,
            response_time=response_time,
            total_results=len(synonyms)
        )
        
        logging.info(f"✅ Retrieved {len(synonyms)} synonyms")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata=metadata.model_dump()
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Synonym retrieval failed: {str(e)}"
        logging.error(f"PubChem error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "api_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def search_similar_compounds(
    cid: int,
    similarity_threshold: float = 0.9,
    max_results: int = 10
) -> Union[str, TextContent]:
    """
    Find structurally similar compounds.
    
    Args:
        cid: Reference compound CID
        similarity_threshold: Minimum similarity (0.0-1.0)
        max_results: Maximum results (1-50)
        
    Returns:
        TextContent with similar compounds
    """
    try:
        if not cid or cid <= 0:
            raise ValueError("Valid PubChem CID is required")
        
        similarity_threshold = max(0.0, min(similarity_threshold, 1.0))
        max_results = max(1, min(max_results, 50))
        
        logging.info(f"🔬 Searching similar compounds to CID: {cid}")
        
        client = get_client()
        threshold_percent = int(similarity_threshold * 100)
        url = f"{client.base_url}/compound/fastsimilarity_2d/cid/{cid}/property/Title,MolecularFormula,MolecularWeight/JSON"
        params = {
            "Threshold": threshold_percent,
            "MaxRecords": max_results
        }
        
        data, response_time = client.make_request(url, params)
        
        similar_compounds = []
        if data and "PropertyTable" in data and "Properties" in data["PropertyTable"]:
            properties_list = data["PropertyTable"]["Properties"]
            
            for prop in properties_list:
                if prop.get("CID") != cid:
                    compound = CompoundData(
                        cid=prop.get("CID"),
                        name=prop.get("Title"),
                        molecular_formula=prop.get("MolecularFormula"),
                        molecular_weight=prop.get("MolecularWeight")
                    )
                    similar_compounds.append(compound)
        
        result = {
            "reference_cid": cid,
            "similarity_threshold": similarity_threshold,
            "similar_compounds": [c.model_dump() for c in similar_compounds],
            "count": len(similar_compounds)
        }
        
        metadata = PubChemMetadata(
            query_type="similarity",
            query_value=str(cid),
            api_endpoint=url,
            response_time=response_time,
            total_results=len(similar_compounds)
        )
        
        logging.info(f"✅ Found {len(similar_compounds)} similar compounds")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata=metadata.model_dump()
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Similarity search failed: {str(e)}"
        logging.error(f"PubChem error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "api_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
