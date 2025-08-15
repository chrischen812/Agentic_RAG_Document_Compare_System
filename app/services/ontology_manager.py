"""
Ontology management service for domain-specific knowledge structures.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import owlready2 as owl
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

from app.core.config import settings

@dataclass
class OntologyClass:
    """Represents an ontology class with relationships."""
    name: str
    label: str
    description: str
    parent_classes: List[str]
    properties: List[str]
    instances: List[str]

@dataclass
class OntologyStructure:
    """Complete ontology structure."""
    domain: str
    classes: Dict[str, OntologyClass]
    properties: Dict[str, Dict[str, Any]]
    individuals: Dict[str, Dict[str, Any]]
    namespace: str

class OntologyManager:
    """Manages domain-specific ontologies for document classification and analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ontologies: Dict[str, OntologyStructure] = {}
        self.base_path = settings.ontology_base_path
    
    async def initialize(self):
        """Initialize ontology manager and load available ontologies."""
        try:
            # Create base ontologies if they don't exist
            await self._create_base_ontologies()
            
            # Load existing ontologies
            await self._load_ontologies()
            
            self.logger.info(f"Loaded {len(self.ontologies)} ontologies")
            
        except Exception as e:
            self.logger.error(f"Error initializing ontology manager: {str(e)}")
            raise
    
    async def get_ontology_for_domain(self, domain: str) -> Optional[OntologyStructure]:
        """Get ontology structure for a specific domain."""
        return self.ontologies.get(domain)
    
    async def list_available_ontologies(self) -> Dict[str, Dict[str, Any]]:
        """List all available ontologies with metadata."""
        result = {}
        for domain, ontology in self.ontologies.items():
            result[domain] = {
                "domain": domain,
                "namespace": ontology.namespace,
                "classes_count": len(ontology.classes),
                "properties_count": len(ontology.properties),
                "individuals_count": len(ontology.individuals)
            }
        return result
    
    async def map_concepts_to_ontology(self, concepts: List[str], domain: str) -> Dict[str, str]:
        """Map extracted concepts to ontology classes with intelligent reasoning."""
        if domain not in self.ontologies:
            return {}
        
        ontology = self.ontologies[domain]
        mappings = {}
        
        for concept in concepts:
            concept_lower = concept.lower()
            
            # Enhanced mapping logic for healthcare domain
            if domain == "healthcare":
                mappings.update(self._map_healthcare_concepts(concept, concept_lower, ontology))
            elif domain == "legal":
                mappings.update(self._map_legal_concepts(concept, concept_lower, ontology))
            elif domain == "financial":
                mappings.update(self._map_financial_concepts(concept, concept_lower, ontology))
            else:
                # Generic mapping
                mappings[concept] = self._find_best_class_match(concept_lower, ontology)
        
        return mappings
    
    def _map_healthcare_concepts(self, concept: str, concept_lower: str, ontology: OntologyStructure) -> Dict[str, str]:
        """Enhanced healthcare concept mapping with semantic understanding."""
        mappings = {}
        
        # Financial cost mappings with context awareness
        if any(term in concept_lower for term in ['premium', 'monthly premium', 'annual premium']):
            mappings[concept] = "healthcare:Premium"
            mappings[f"{concept}_frequency"] = "monthly" if "monthly" in concept_lower else "annual"
        
        elif any(term in concept_lower for term in ['deductible', 'annual deductible', 'family deductible']):
            mappings[concept] = "healthcare:Deductible"
            mappings[f"{concept}_scope"] = "family" if "family" in concept_lower else "individual"
        
        elif any(term in concept_lower for term in ['copay', 'copayment', 'co-pay']):
            mappings[concept] = "healthcare:Copayment"
            # Determine service type from context
            if any(svc in concept_lower for svc in ['primary care', 'doctor visit', 'office visit']):
                mappings[f"{concept}_service"] = "healthcare:PrimaryCareService"
            elif any(svc in concept_lower for svc in ['specialist', 'specialty']):
                mappings[f"{concept}_service"] = "healthcare:SpecialistService"
            elif any(svc in concept_lower for svc in ['emergency', 'er', 'urgent']):
                mappings[f"{concept}_service"] = "healthcare:EmergencyService"
        
        elif any(term in concept_lower for term in ['out-of-pocket', 'out of pocket', 'oop maximum']):
            mappings[concept] = "healthcare:OutOfPocketMaximum"
        
        elif any(term in concept_lower for term in ['coinsurance', 'co-insurance']):
            mappings[concept] = "healthcare:Coinsurance"
        
        # Service mappings with enhanced context
        elif any(term in concept_lower for term in ['primary care', 'family doctor', 'general practitioner']):
            mappings[concept] = "healthcare:PrimaryCareService"
        
        elif any(term in concept_lower for term in ['specialist', 'cardiology', 'dermatology', 'orthopedic']):
            mappings[concept] = "healthcare:SpecialistService"
        
        elif any(term in concept_lower for term in ['emergency', 'er visit', 'urgent care']):
            mappings[concept] = "healthcare:EmergencyService"
        
        elif any(term in concept_lower for term in ['prescription', 'medication', 'drug coverage', 'pharmacy']):
            mappings[concept] = "healthcare:Medication"
            if any(tier in concept_lower for tier in ['generic', 'tier 1']):
                mappings[f"{concept}_tier"] = "generic"
            elif any(tier in concept_lower for tier in ['brand', 'tier 2', 'preferred']):
                mappings[f"{concept}_tier"] = "preferred_brand"
            elif any(tier in concept_lower for tier in ['non-preferred', 'tier 3']):
                mappings[f"{concept}_tier"] = "non_preferred"
        
        # Plan type detection
        elif any(term in concept_lower for term in ['hmo', 'health maintenance']):
            mappings[concept] = "healthcare:HMO"
        elif any(term in concept_lower for term in ['ppo', 'preferred provider']):
            mappings[concept] = "healthcare:PPO"
        elif any(term in concept_lower for term in ['epo', 'exclusive provider']):
            mappings[concept] = "healthcare:EPO"
        elif any(term in concept_lower for term in ['high deductible', 'hdhp', 'hsa']):
            mappings[concept] = "healthcare:HDHP"
        
        # Provider and network mappings
        elif any(term in concept_lower for term in ['network', 'in-network', 'provider network']):
            mappings[concept] = "healthcare:Provider"
            mappings[f"{concept}_network_type"] = "in_network" if "in-network" in concept_lower else "provider_network"
        
        # Benefit and coverage mappings
        elif any(term in concept_lower for term in ['benefit', 'coverage', 'covered service']):
            mappings[concept] = "healthcare:Benefit"
        
        elif any(term in concept_lower for term in ['exclusion', 'not covered', 'excluded']):
            mappings[concept] = "healthcare:Exclusion"
        
        elif any(term in concept_lower for term in ['limitation', 'limit', 'restricted']):
            mappings[concept] = "healthcare:Limitation"
        
        return mappings
    
    def _map_legal_concepts(self, concept: str, concept_lower: str, ontology: OntologyStructure) -> Dict[str, str]:
        """Enhanced legal concept mapping."""
        mappings = {}
        
        # Contract and agreement mappings
        if any(term in concept_lower for term in ['contract', 'agreement', 'terms']):
            mappings[concept] = "legal:Contract"
        elif any(term in concept_lower for term in ['clause', 'provision', 'section']):
            mappings[concept] = "legal:Clause"
        elif any(term in concept_lower for term in ['liability', 'responsibility', 'obligation']):
            mappings[concept] = "legal:Liability"
        elif any(term in concept_lower for term in ['jurisdiction', 'governing law', 'applicable law']):
            mappings[concept] = "legal:Jurisdiction"
        
        return mappings
    
    def _map_financial_concepts(self, concept: str, concept_lower: str, ontology: OntologyStructure) -> Dict[str, str]:
        """Enhanced financial concept mapping."""
        mappings = {}
        
        # Investment and financial instrument mappings
        if any(term in concept_lower for term in ['investment', 'portfolio', 'asset']):
            mappings[concept] = "financial:Investment"
        elif any(term in concept_lower for term in ['risk', 'volatility', 'exposure']):
            mappings[concept] = "financial:Risk"
        elif any(term in concept_lower for term in ['return', 'yield', 'performance']):
            mappings[concept] = "financial:Return"
        elif any(term in concept_lower for term in ['fee', 'expense', 'cost']):
            mappings[concept] = "financial:Fee"
        
        return mappings
    
    def _find_best_class_match(self, concept_lower: str, ontology: OntologyStructure) -> str:
        """Find the best matching ontology class using semantic similarity."""
        best_match = "Unknown"
        best_score = 0
        
        for class_name, class_info in ontology.classes.items():
            # Simple semantic matching based on keywords
            class_terms = [class_info.label.lower(), class_info.description.lower()]
            class_terms.extend([prop.lower() for prop in class_info.properties])
            
            score = sum(1 for term in class_terms if any(word in term for word in concept_lower.split()))
            
            if score > best_score:
                best_score = score
                best_match = class_name
        
        return best_match
    
    async def get_semantic_relationships(self, concept1: str, concept2: str, domain: str) -> Dict[str, Any]:
        """Analyze semantic relationships between concepts."""
        if domain not in self.ontologies:
            return {}
        
        ontology = self.ontologies[domain]
        mappings1 = await self.map_concepts_to_ontology([concept1], domain)
        mappings2 = await self.map_concepts_to_ontology([concept2], domain)
        
        class1 = mappings1.get(concept1, "Unknown")
        class2 = mappings2.get(concept2, "Unknown")
        
        relationships = {
            "concepts": [concept1, concept2],
            "ontology_classes": [class1, class2],
            "relationship_type": self._determine_relationship_type(class1, class2, domain),
            "semantic_distance": self._calculate_semantic_distance(class1, class2, ontology),
            "contextual_insights": self._generate_contextual_insights(concept1, concept2, class1, class2, domain)
        }
        
        return relationships
    
    def _determine_relationship_type(self, class1: str, class2: str, domain: str) -> str:
        """Determine the type of relationship between two ontology classes."""
        if domain == "healthcare":
            # Cost relationships
            cost_classes = ["Premium", "Deductible", "Copayment", "Coinsurance", "OutOfPocketMaximum"]
            if any(c in class1 for c in cost_classes) and any(c in class2 for c in cost_classes):
                return "financial_relationship"
            
            # Service relationships
            service_classes = ["PrimaryCareService", "SpecialistService", "EmergencyService"]
            if any(c in class1 for c in service_classes) and any(c in class2 for c in service_classes):
                return "service_hierarchy"
            
            # Plan relationships
            plan_classes = ["HMO", "PPO", "EPO", "HDHP"]
            if any(c in class1 for c in plan_classes) and any(c in class2 for c in plan_classes):
                return "plan_comparison"
        
        return "semantic_association"
    
    def _calculate_semantic_distance(self, class1: str, class2: str, ontology: OntologyStructure) -> float:
        """Calculate semantic distance between two classes."""
        if class1 == class2:
            return 0.0
        
        # Simple heuristic based on class hierarchy
        if class1 in ontology.classes and class2 in ontology.classes:
            parents1 = ontology.classes[class1].parent_classes
            parents2 = ontology.classes[class2].parent_classes
            
            # Check for shared parent classes
            shared_parents = set(parents1) & set(parents2)
            if shared_parents:
                return 0.3  # Close relationship
            
            # Check if one is parent of the other
            if class1 in parents2 or class2 in parents1:
                return 0.2  # Very close relationship
        
        return 0.8  # Distant relationship
    
    def _generate_contextual_insights(self, concept1: str, concept2: str, class1: str, class2: str, domain: str) -> List[str]:
        """Generate contextual insights about the relationship."""
        insights = []
        
        if domain == "healthcare":
            # Financial insights
            if "Premium" in class1 and "Deductible" in class2:
                insights.append("Premium and deductible work together to determine your total healthcare costs")
                insights.append("Lower premiums typically mean higher deductibles and vice versa")
            
            elif "Copayment" in class1 and "Coinsurance" in class2:
                insights.append("Copayments are fixed amounts while coinsurance is a percentage of costs")
                insights.append("Some plans use copayments for certain services and coinsurance for others")
            
            elif "OutOfPocketMaximum" in class1 or "OutOfPocketMaximum" in class2:
                insights.append("Out-of-pocket maximum provides financial protection by capping your annual costs")
                insights.append("Once reached, insurance pays 100% of covered services")
            
            # Service insights
            elif "PrimaryCareService" in class1 and "SpecialistService" in class2:
                insights.append("Primary care typically has lower copayments than specialist visits")
                insights.append("Many plans require referrals from primary care to see specialists")
            
            elif "EmergencyService" in class1 or "EmergencyService" in class2:
                insights.append("Emergency services usually have higher cost-sharing but are covered without referrals")
                insights.append("Consider urgent care alternatives for non-emergency situations")
        
        return insights
    
    def _find_best_ontology_match(self, concept: str, ontology: OntologyStructure) -> Optional[str]:
        """Find the best matching ontology class for a concept."""
        concept_lower = concept.lower()
        
        # Direct name match
        for class_name, ont_class in ontology.classes.items():
            if concept_lower == ont_class.name.lower():
                return class_name
        
        # Label match
        for class_name, ont_class in ontology.classes.items():
            if concept_lower in ont_class.label.lower():
                return class_name
        
        # Description match
        for class_name, ont_class in ontology.classes.items():
            if concept_lower in ont_class.description.lower():
                return class_name
        
        return None
    
    async def _load_ontologies(self):
        """Load ontologies from OWL files."""
        ontology_files = {
            "healthcare": "healthcare.owl",
            "legal": "legal.owl", 
            "financial": "financial.owl"
        }
        
        for domain, filename in ontology_files.items():
            file_path = os.path.join(self.base_path, filename)
            if os.path.exists(file_path):
                try:
                    ontology = await self._load_owl_file(file_path, domain)
                    self.ontologies[domain] = ontology
                except Exception as e:
                    self.logger.error(f"Error loading {domain} ontology: {str(e)}")
    
    async def _load_owl_file(self, file_path: str, domain: str) -> OntologyStructure:
        """Load an OWL file and parse it into our structure."""
        try:
            # Load with rdflib for better parsing
            g = Graph()
            g.parse(file_path, format="xml")
            
            # Extract namespace
            namespace = str(list(g.namespaces())[0][1]) if list(g.namespaces()) else f"http://example.com/{domain}#"
            
            # Parse classes
            classes = {}
            for subject in g.subjects(RDF.type, OWL.Class):
                class_name = str(subject).split('#')[-1] if '#' in str(subject) else str(subject).split('/')[-1]
                
                # Get label
                label = ""
                for obj in g.objects(subject, RDFS.label):
                    label = str(obj)
                    break
                
                # Get comment (description)
                description = ""
                for obj in g.objects(subject, RDFS.comment):
                    description = str(obj)
                    break
                
                # Get parent classes
                parent_classes = []
                for obj in g.objects(subject, RDFS.subClassOf):
                    parent_name = str(obj).split('#')[-1] if '#' in str(obj) else str(obj).split('/')[-1]
                    parent_classes.append(parent_name)
                
                classes[class_name] = OntologyClass(
                    name=class_name,
                    label=label or class_name,
                    description=description,
                    parent_classes=parent_classes,
                    properties=[],
                    instances=[]
                )
            
            # Parse properties
            properties = {}
            for subject in g.subjects(RDF.type, OWL.ObjectProperty):
                prop_name = str(subject).split('#')[-1] if '#' in str(subject) else str(subject).split('/')[-1]
                
                prop_data = {
                    "name": prop_name,
                    "type": "object_property",
                    "domain": [],
                    "range": []
                }
                
                # Get domain and range
                for obj in g.objects(subject, RDFS.domain):
                    domain_class = str(obj).split('#')[-1] if '#' in str(obj) else str(obj).split('/')[-1]
                    prop_data["domain"].append(domain_class)
                
                for obj in g.objects(subject, RDFS.range):
                    range_class = str(obj).split('#')[-1] if '#' in str(obj) else str(obj).split('/')[-1]
                    prop_data["range"].append(range_class)
                
                properties[prop_name] = prop_data
            
            # Parse individuals
            individuals = {}
            for subject in g.subjects():
                # Check if it's an individual (not a class or property)
                is_individual = False
                for class_uri in g.objects(subject, RDF.type):
                    if str(class_uri) not in [str(OWL.Class), str(OWL.ObjectProperty), str(OWL.DatatypeProperty)]:
                        is_individual = True
                        break
                
                if is_individual:
                    ind_name = str(subject).split('#')[-1] if '#' in str(subject) else str(subject).split('/')[-1]
                    individuals[ind_name] = {
                        "name": ind_name,
                        "types": [str(obj) for obj in g.objects(subject, RDF.type)]
                    }
            
            return OntologyStructure(
                domain=domain,
                classes=classes,
                properties=properties,
                individuals=individuals,
                namespace=namespace
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing OWL file {file_path}: {str(e)}")
            # Return empty ontology structure
            return OntologyStructure(
                domain=domain,
                classes={},
                properties={},
                individuals={},
                namespace=f"http://example.com/{domain}#"
            )
    
    async def _create_base_ontologies(self):
        """Create base ontologies if they don't exist."""
        base_ontologies = {
            "healthcare": self._create_healthcare_ontology,
            "legal": self._create_legal_ontology,
            "financial": self._create_financial_ontology
        }
        
        for domain, creator_func in base_ontologies.items():
            file_path = os.path.join(self.base_path, f"{domain}.owl")
            if not os.path.exists(file_path):
                try:
                    await creator_func(file_path)
                    self.logger.info(f"Created base ontology for {domain}")
                except Exception as e:
                    self.logger.error(f"Error creating {domain} ontology: {str(e)}")
    
    async def _create_healthcare_ontology(self, file_path: str):
        """Create a base healthcare ontology."""
        # This creates the content that would be in the healthcare.owl file
        # For now, we'll store the structure and let the file creation happen elsewhere
        pass
    
    async def _create_legal_ontology(self, file_path: str):
        """Create a base legal ontology."""
        pass
    
    async def _create_financial_ontology(self, file_path: str):
        """Create a base financial ontology."""
        pass
