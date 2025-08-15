"""
Base ontology utilities for creating and managing domain-specific ontologies.
"""
import os
from typing import Dict, List, Any
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD

class BaseOntologyBuilder:
    """Utility class for building domain-specific ontologies."""
    
    def __init__(self, domain: str, namespace_uri: str):
        self.domain = domain
        self.namespace = Namespace(namespace_uri)
        self.graph = Graph()
        
        # Bind common namespaces
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        self.graph.bind(domain, self.namespace)
        
        # Add ontology declaration
        self.graph.add((URIRef(namespace_uri), RDF.type, OWL.Ontology))
    
    def add_class(self, class_name: str, label: str = None, comment: str = None, parent_class: str = None):
        """Add a class to the ontology."""
        class_uri = self.namespace[class_name]
        
        # Add class declaration
        self.graph.add((class_uri, RDF.type, OWL.Class))
        
        # Add label
        if label:
            self.graph.add((class_uri, RDFS.label, Literal(label, lang="en")))
        
        # Add comment
        if comment:
            self.graph.add((class_uri, RDFS.comment, Literal(comment, lang="en")))
        
        # Add parent class relationship
        if parent_class:
            parent_uri = self.namespace[parent_class]
            self.graph.add((class_uri, RDFS.subClassOf, parent_uri))
    
    def add_object_property(self, property_name: str, label: str = None, comment: str = None, 
                           domain_class: str = None, range_class: str = None):
        """Add an object property to the ontology."""
        property_uri = self.namespace[property_name]
        
        # Add property declaration
        self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
        
        # Add label
        if label:
            self.graph.add((property_uri, RDFS.label, Literal(label, lang="en")))
        
        # Add comment
        if comment:
            self.graph.add((property_uri, RDFS.comment, Literal(comment, lang="en")))
        
        # Add domain
        if domain_class:
            domain_uri = self.namespace[domain_class]
            self.graph.add((property_uri, RDFS.domain, domain_uri))
        
        # Add range
        if range_class:
            range_uri = self.namespace[range_class]
            self.graph.add((property_uri, RDFS.range, range_uri))
    
    def add_datatype_property(self, property_name: str, label: str = None, comment: str = None,
                             domain_class: str = None, range_type: str = "string"):
        """Add a datatype property to the ontology."""
        property_uri = self.namespace[property_name]
        
        # Add property declaration
        self.graph.add((property_uri, RDF.type, OWL.DatatypeProperty))
        
        # Add label
        if label:
            self.graph.add((property_uri, RDFS.label, Literal(label, lang="en")))
        
        # Add comment
        if comment:
            self.graph.add((property_uri, RDFS.comment, Literal(comment, lang="en")))
        
        # Add domain
        if domain_class:
            domain_uri = self.namespace[domain_class]
            self.graph.add((property_uri, RDFS.domain, domain_uri))
        
        # Add range (datatype)
        range_mapping = {
            "string": XSD.string,
            "integer": XSD.integer,
            "float": XSD.float,
            "boolean": XSD.boolean,
            "date": XSD.date,
            "datetime": XSD.dateTime
        }
        range_uri = range_mapping.get(range_type, XSD.string)
        self.graph.add((property_uri, RDFS.range, range_uri))
    
    def add_individual(self, individual_name: str, class_name: str, label: str = None):
        """Add an individual (instance) to the ontology."""
        individual_uri = self.namespace[individual_name]
        class_uri = self.namespace[class_name]
        
        # Add individual declaration
        self.graph.add((individual_uri, RDF.type, class_uri))
        
        # Add label
        if label:
            self.graph.add((individual_uri, RDFS.label, Literal(label, lang="en")))
    
    def save_to_file(self, file_path: str):
        """Save the ontology to an OWL file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.graph.serialize(destination=file_path, format="xml")

def create_healthcare_ontology(file_path: str):
    """Create a comprehensive healthcare ontology."""
    builder = BaseOntologyBuilder("healthcare", "http://example.com/healthcare#")
    
    # Top-level classes
    builder.add_class("Document", "Healthcare Document", "Base class for all healthcare documents")
    builder.add_class("Coverage", "Coverage", "Insurance coverage information")
    builder.add_class("Benefit", "Benefit", "Healthcare benefit or service")
    builder.add_class("Limitation", "Limitation", "Coverage limitation or restriction")
    builder.add_class("Exclusion", "Exclusion", "Coverage exclusion")
    builder.add_class("Provider", "Healthcare Provider", "Healthcare service provider")
    builder.add_class("Condition", "Medical Condition", "Medical condition or diagnosis")
    builder.add_class("Treatment", "Medical Treatment", "Medical treatment or procedure")
    builder.add_class("Medication", "Medication", "Pharmaceutical medication")
    
    # Document types
    builder.add_class("InsurancePolicy", "Insurance Policy", "Health insurance policy document", "Document")
    builder.add_class("BenefitsSummary", "Benefits Summary", "Summary of health benefits", "Document")
    builder.add_class("ClaimForm", "Claim Form", "Insurance claim form", "Document")
    builder.add_class("MedicalRecord", "Medical Record", "Patient medical record", "Document")
    
    # Coverage types
    builder.add_class("MedicalCoverage", "Medical Coverage", "General medical coverage", "Coverage")
    builder.add_class("DentalCoverage", "Dental Coverage", "Dental care coverage", "Coverage")
    builder.add_class("VisionCoverage", "Vision Coverage", "Vision care coverage", "Coverage")
    builder.add_class("MentalHealthCoverage", "Mental Health Coverage", "Mental health services coverage", "Coverage")
    builder.add_class("PrescriptionCoverage", "Prescription Coverage", "Prescription drug coverage", "Coverage")
    
    # Properties
    builder.add_object_property("hasCoverage", "has coverage", "Document has coverage type", "Document", "Coverage")
    builder.add_object_property("hasBenefit", "has benefit", "Coverage includes benefit", "Coverage", "Benefit")
    builder.add_object_property("hasLimitation", "has limitation", "Coverage has limitation", "Coverage", "Limitation")
    builder.add_object_property("hasExclusion", "has exclusion", "Coverage excludes service", "Coverage", "Exclusion")
    builder.add_object_property("coversCondition", "covers condition", "Coverage applies to condition", "Coverage", "Condition")
    builder.add_object_property("coversTreatment", "covers treatment", "Coverage applies to treatment", "Coverage", "Treatment")
    
    # Datatype properties
    builder.add_datatype_property("deductibleAmount", "deductible amount", "Insurance deductible amount", "Coverage", "float")
    builder.add_datatype_property("copayAmount", "copay amount", "Copayment amount", "Benefit", "float")
    builder.add_datatype_property("coveragePercentage", "coverage percentage", "Percentage of coverage", "Coverage", "float")
    builder.add_datatype_property("maximumBenefit", "maximum benefit", "Maximum benefit amount", "Benefit", "float")
    builder.add_datatype_property("policyNumber", "policy number", "Insurance policy number", "InsurancePolicy", "string")
    
    builder.save_to_file(file_path)
