"""
Drug Formulary Lookup Tool.

Provides access to institutional drug formulary for validating
drug dosages and protocols in IACUC submissions.
"""

import json
from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class DrugInfo(BaseModel):
    """Information about a drug from the formulary."""
    
    name: str = Field(description="Drug name")
    drug_class: str = Field(description="Drug classification")
    dea_schedule: str = Field(description="DEA schedule if controlled")
    dose_range: Optional[str] = Field(default=None, description="Approved dose range")
    route: Optional[str] = Field(default=None, description="Administration route")
    onset: Optional[str] = Field(default=None, description="Onset of action")
    duration: Optional[str] = Field(default=None, description="Duration of effect")
    notes: Optional[str] = Field(default=None, description="Species-specific notes")
    contraindications: list[str] = Field(default_factory=list)


class FormularyLookupResult(BaseModel):
    """Result of a formulary lookup."""
    
    found: bool = Field(description="Whether drug was found in formulary")
    drug_info: Optional[DrugInfo] = Field(default=None)
    species_specific: bool = Field(default=False)
    message: str = Field(default="")


class DrugFormulary:
    """
    Drug formulary manager.
    
    Loads and queries the institutional drug formulary.
    """
    
    def __init__(self, formulary_path: Optional[str | Path] = None):
        """
        Initialize formulary from file.
        
        Args:
            formulary_path: Path to formulary JSON file. If None, uses default.
        """
        if formulary_path is None:
            # Use default sample formulary
            formulary_path = Path(__file__).parent.parent.parent / \
                "knowledge_base" / "formulary" / "sample_drug_formulary.json"
        
        self.formulary_path = Path(formulary_path)
        self.data = self._load_formulary()
    
    def _load_formulary(self) -> dict:
        """Load formulary data from file."""
        if not self.formulary_path.exists():
            return {"drugs": [], "combination_protocols": [], "emergency_drugs": []}
        
        with open(self.formulary_path, "r") as f:
            return json.load(f)
    
    def lookup_drug(
        self,
        drug_name: str,
        species: Optional[str] = None,
    ) -> FormularyLookupResult:
        """
        Look up a drug in the formulary.
        
        Args:
            drug_name: Name of the drug to look up
            species: Optional species for species-specific dosing
            
        Returns:
            FormularyLookupResult with drug information.
        """
        drug_name_lower = drug_name.lower()
        
        for drug in self.data.get("drugs", []):
            if drug["name"].lower() == drug_name_lower:
                # Found the drug
                info = DrugInfo(
                    name=drug["name"],
                    drug_class=drug.get("class", "Unknown"),
                    dea_schedule=drug.get("dea_schedule", "Not scheduled"),
                    contraindications=drug.get("contraindications", []),
                )
                
                # Add species-specific info if available
                species_key = species.lower().replace(" ", "_") if species else None
                species_dosing = drug.get("species_dosing", {})
                
                if species_key and species_key in species_dosing:
                    sp_info = species_dosing[species_key]
                    info.dose_range = sp_info.get("dose_range")
                    info.route = sp_info.get("route")
                    info.onset = sp_info.get("onset")
                    info.duration = sp_info.get("duration")
                    info.notes = sp_info.get("notes")
                    
                    return FormularyLookupResult(
                        found=True,
                        drug_info=info,
                        species_specific=True,
                        message=f"Found {drug_name} with {species}-specific dosing",
                    )
                else:
                    # Drug found but no species-specific info
                    return FormularyLookupResult(
                        found=True,
                        drug_info=info,
                        species_specific=False,
                        message=f"Found {drug_name} (no species-specific dosing for {species})" 
                                if species else f"Found {drug_name}",
                    )
        
        return FormularyLookupResult(
            found=False,
            message=f"Drug '{drug_name}' not found in formulary",
        )
    
    def get_combination_protocol(self, protocol_name: str) -> Optional[dict]:
        """
        Get a combination protocol by name.
        
        Args:
            protocol_name: Name or partial name of protocol
            
        Returns:
            Protocol dict if found, None otherwise.
        """
        name_lower = protocol_name.lower()
        
        for protocol in self.data.get("combination_protocols", []):
            if name_lower in protocol["name"].lower():
                return protocol
        
        return None
    
    def list_drugs_for_species(self, species: str) -> list[str]:
        """
        List all drugs with dosing info for a species.
        
        Args:
            species: Species name
            
        Returns:
            List of drug names with species-specific dosing.
        """
        species_key = species.lower().replace(" ", "_")
        drugs = []
        
        for drug in self.data.get("drugs", []):
            if species_key in drug.get("species_dosing", {}):
                drugs.append(drug["name"])
        
        return drugs
    
    def validate_dose(
        self,
        drug_name: str,
        species: str,
        proposed_dose: str,
    ) -> dict:
        """
        Validate a proposed dose against the formulary.
        
        Args:
            drug_name: Name of the drug
            species: Species
            proposed_dose: Proposed dose (e.g., "100 mg/kg")
            
        Returns:
            Dictionary with validation result.
        """
        lookup = self.lookup_drug(drug_name, species)
        
        if not lookup.found:
            return {
                "valid": False,
                "status": "NOT_FOUND",
                "message": f"Drug '{drug_name}' not found in formulary",
            }
        
        if not lookup.species_specific:
            return {
                "valid": False,
                "status": "NO_SPECIES_DATA",
                "message": f"No dosing data for {species} in formulary",
            }
        
        # Parse proposed dose
        try:
            proposed_value = float(proposed_dose.split()[0].replace(",", ""))
        except (ValueError, IndexError):
            return {
                "valid": False,
                "status": "PARSE_ERROR",
                "message": f"Could not parse proposed dose: {proposed_dose}",
            }
        
        # Parse formulary range
        formulary_range = lookup.drug_info.dose_range
        if not formulary_range:
            return {
                "valid": False,
                "status": "NO_RANGE",
                "message": "No dose range specified in formulary",
            }
        
        try:
            # Handle ranges like "80-100 mg/kg" or single values
            range_part = formulary_range.split()[0]
            if "-" in range_part:
                low, high = range_part.split("-")
                low_val = float(low)
                high_val = float(high)
            else:
                low_val = float(range_part) * 0.8  # Allow 20% below single value
                high_val = float(range_part) * 1.2  # Allow 20% above single value
        except ValueError:
            return {
                "valid": False,
                "status": "RANGE_PARSE_ERROR", 
                "message": f"Could not parse formulary range: {formulary_range}",
            }
        
        # Check if proposed dose is within range
        if low_val <= proposed_value <= high_val:
            return {
                "valid": True,
                "status": "APPROVED",
                "message": f"Dose {proposed_dose} is within approved range ({formulary_range})",
                "approved_range": formulary_range,
            }
        elif proposed_value < low_val:
            return {
                "valid": False,
                "status": "BELOW_RANGE",
                "message": f"Dose {proposed_dose} is below approved range ({formulary_range})",
                "approved_range": formulary_range,
            }
        else:
            return {
                "valid": False,
                "status": "ABOVE_RANGE",
                "message": f"Dose {proposed_dose} is above approved range ({formulary_range})",
                "approved_range": formulary_range,
            }
    
    def get_emergency_drugs(self) -> list[dict]:
        """Get list of emergency drugs."""
        return self.data.get("emergency_drugs", [])


class FormularyLookupTool(BaseTool):
    """
    Tool for looking up drug information from the institutional formulary.
    
    Used by agents to validate drug dosages and find approved protocols.
    """
    
    name: str = "formulary_lookup"
    description: str = (
        "Look up drug dosing information from the institutional formulary. "
        "Input format: 'drug_name' or 'drug_name for species'. "
        "Example: 'ketamine for mouse' or 'buprenorphine'"
    )
    
    formulary: Optional[DrugFormulary] = None
    
    def __init__(self, formulary_path: Optional[str] = None, **kwargs):
        """Initialize with optional custom formulary path."""
        super().__init__(**kwargs)
        self.formulary = DrugFormulary(formulary_path)
    
    def _run(self, query: str) -> str:
        """
        Look up drug information.
        
        Args:
            query: Drug name and optionally species
            
        Returns:
            Formatted drug information.
        """
        # Parse query
        query_lower = query.lower()
        species = None
        drug_name = query
        
        if " for " in query_lower:
            parts = query_lower.split(" for ")
            drug_name = parts[0].strip()
            species = parts[1].strip()
        
        result = self.formulary.lookup_drug(drug_name, species)
        
        if not result.found:
            return f"Drug not found: {drug_name}\n\nAvailable drugs in formulary for validation."
        
        # Format output
        info = result.drug_info
        output = [
            f"FORMULARY INFORMATION: {info.name}",
            "=" * 50,
            "",
            f"Drug Class: {info.drug_class}",
            f"DEA Schedule: {info.dea_schedule}",
        ]
        
        if result.species_specific:
            output.extend([
                "",
                f"Species: {species.upper()}",
                f"Dose Range: {info.dose_range}",
                f"Route: {info.route}",
                f"Onset: {info.onset}",
                f"Duration: {info.duration}",
            ])
            if info.notes:
                output.append(f"Notes: {info.notes}")
        else:
            output.append("\nNo species-specific dosing available.")
        
        if info.contraindications:
            output.extend([
                "",
                "Contraindications:",
            ])
            for contra in info.contraindications:
                output.append(f"  • {contra}")
        
        return "\n".join(output)


# Export key items
__all__ = [
    "FormularyLookupTool",
    "DrugFormulary",
    "DrugInfo",
    "FormularyLookupResult",
]
