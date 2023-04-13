# generated by datamodel-codegen:
#   filename:  swagger.yaml
#   timestamp: 2023-04-06T11:54:49+00:00

from __future__ import annotations

from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt, StrictStr
from typing_extensions import Literal


class LocationItem(BaseModel):
    __root__: Annotated[
        StrictStr,
        Field(
            description='This element is deprecated because it is XML specific. It is replaced by issue.expression, which is format independent, and simpler to parse. \n\nFor resource issues, this will be a simple XPath limited to element names, repetition indicators and the default child accessor that identifies one of the elements in the resource that caused this issue to be raised.  For HTTP errors, will be "http." + the parameter name.'
        ),
    ]


class ExpressionItem(BaseModel):
    __root__: Annotated[
        StrictStr,
        Field(
            description="A [simple subset of FHIRPath](fhirpath.html#simple) limited to element names, repetition indicators and the default child accessor that identifies one of the elements in the resource that caused this issue to be raised."
        ),
    ]


class BundleEntryRequest(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    method: Annotated[
        StrictStr,
        Field(
            description="In a transaction or batch, this is the HTTP action to be executed for this entry. In a history bundle, this indicates the HTTP action that occurred."
        ),
    ]
    url: Annotated[
        StrictStr,
        Field(
            description="The URL for this entry, relative to the root (the address to which the request is posted)."
        ),
    ]
    ifNoneMatch: Annotated[
        Optional[StrictStr],
        Field(
            description='If the ETag values match, return a 304 Not Modified status. See the API documentation for ["Conditional Read"](http.html#cread).'
        ),
    ] = None
    ifModifiedSince: Annotated[
        Optional[StrictStr],
        Field(
            description='Only perform the operation if the last updated date matches. See the API documentation for ["Conditional Read"](http.html#cread).'
        ),
    ] = None
    ifMatch: Annotated[
        Optional[StrictStr],
        Field(
            description='Only perform the operation if the Etag value matches. For more information, see the API section ["Managing Resource Contention"](http.html#concurrency).'
        ),
    ] = None
    ifNoneExist: Annotated[
        Optional[StrictStr],
        Field(
            description='Instruct the server not to perform the create if a specified resource already exists. For further information, see the API documentation for ["Conditional Create"](http.html#ccreate). This is just the query portion of the URL &ndash; what follows the "?" (not including the "?").'
        ),
    ] = None


class BundleEntrySearch(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    mode: Annotated[
        Optional[StrictStr],
        Field(
            description="Why this entry is in the result set &ndash; whether it's included as a match or because of an _include requirement, or to convey information or warning information about the search process."
        ),
    ] = None
    score: Annotated[
        Optional[StrictFloat],
        Field(
            description="When searching, the server's search ranking score for the entry."
        ),
    ] = None


class BundleLink(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    relation: Annotated[
        StrictStr,
        Field(
            description="A name which details the functional use for this link &ndash; see [http://www.iana.org/assignments/link&ndash;relations/link&ndash;relations.xhtml#link&ndash;relations&ndash;1](http://www.iana.org/assignments/link&ndash;relations/link&ndash;relations.xhtml#link&ndash;relations&ndash;1)."
        ),
    ]
    url: Annotated[StrictStr, Field(description="The reference details for the link.")]


class Attachment(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    contentType: Annotated[
        Optional[StrictStr],
        Field(
            description="Identifies the type of the data in the attachment and allows a method to be chosen to interpret or render the data. Includes mime type parameters such as charset where appropriate."
        ),
    ] = None
    language: Annotated[
        Optional[StrictStr],
        Field(
            description="The human language of the content. The value can be any valid value according to BCP 47."
        ),
    ] = None
    data: Annotated[
        Optional[StrictStr],
        Field(
            description="The actual data of the attachment &ndash; a sequence of bytes, base64 encoded."
        ),
    ] = None
    url: Annotated[
        Optional[StrictStr],
        Field(description="A location where the data can be accessed."),
    ] = None
    size: Annotated[
        Optional[StrictInt],
        Field(
            description="The number of bytes of data that make up this attachment (before base64 encoding, if that is done)."
        ),
    ] = None
    hash: Annotated[
        Optional[StrictStr],
        Field(
            description="The calculated hash of the data using SHA&ndash;1. Represented using base64."
        ),
    ] = None
    title: Annotated[
        Optional[StrictStr],
        Field(description="A label or set of text to display in place of the data."),
    ] = None
    creation: Annotated[
        Optional[StrictStr],
        Field(description="The date that the attachment was first created."),
    ] = None


class Coding(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    system: Annotated[
        Optional[StrictStr],
        Field(
            description="The identification of the code system that defines the meaning of the symbol in the code."
        ),
    ] = None
    version: Annotated[
        Optional[StrictStr],
        Field(
            description="The version of the code system which was used when choosing this code. Note that a well&ndash;maintained code system does not need the version reported, because the meaning of codes is consistent across versions. However this cannot consistently be assured, and when the meaning is not guaranteed to be consistent, the version SHOULD be exchanged."
        ),
    ] = None
    code: Annotated[
        Optional[StrictStr],
        Field(
            description="A symbol in syntax defined by the system. The symbol may be a predefined code or an expression in a syntax defined by the coding system (e.g. post&ndash;coordination)."
        ),
    ] = None
    display: Annotated[
        Optional[StrictStr],
        Field(
            description="A representation of the meaning of the code in the system, following the rules of the system."
        ),
    ] = None
    userSelected: Annotated[
        Optional[StrictBool],
        Field(
            description="Indicates that this coding was chosen by a user directly &ndash; e.g. off a pick list of available items (codes or displays)."
        ),
    ] = None


class Period(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    start: Annotated[
        Optional[StrictStr],
        Field(description="The start of the period. The boundary is inclusive."),
    ] = None
    end: Annotated[
        Optional[StrictStr],
        Field(
            description="The end of the period. If the end of the period is missing, it means no end was known or planned at the time the instance was created. The start may be in the past, and the end date in the future, which means that period is expected/planned to end at that time."
        ),
    ] = None


class Quantity(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    value: Annotated[
        Optional[StrictFloat],
        Field(
            description="The value of the measured amount. The value includes an implicit precision in the presentation of the value."
        ),
    ] = None
    comparator: Annotated[
        Optional[StrictStr],
        Field(
            description='How the value should be understood and represented &ndash; whether the actual value is greater or less than the stated value due to measurement issues; e.g. if the comparator is "<" , then the real value is < stated value.'
        ),
    ] = None
    unit: Annotated[
        Optional[StrictStr],
        Field(description="A human&ndash;readable form of the unit."),
    ] = None
    system: Annotated[
        Optional[StrictStr],
        Field(
            description="The identification of the system that provides the coded form of the unit."
        ),
    ] = None
    code: Annotated[
        Optional[StrictStr],
        Field(
            description="A computer processable form of the unit in some unit representation system."
        ),
    ] = None


class ProfileItem(BaseModel):
    __root__: Annotated[
        StrictStr,
        Field(
            description="A list of profiles (references to [StructureDefinition](structuredefinition.html#) resources) that this resource claims to conform to. The URL is a reference to [StructureDefinition.url](structuredefinition&ndash;definitions.html#StructureDefinition.url)."
        ),
    ]


class Meta(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    versionId: Annotated[
        Optional[StrictStr],
        Field(
            description="The version specific identifier, as it appears in the version portion of the URL. This value changes when the resource is created, updated, or deleted."
        ),
    ] = None
    lastUpdated: Annotated[
        Optional[StrictStr],
        Field(
            description="When the resource last changed &ndash; e.g. when the version changed."
        ),
    ] = None
    source: Annotated[
        Optional[StrictStr],
        Field(
            description="A uri that identifies the source system of the resource. This provides a minimal amount of [Provenance](provenance.html#) information that can be used to track or differentiate the source of information in the resource. The source may identify another FHIR server, document, message, database, etc."
        ),
    ] = None
    profile: Optional[List[ProfileItem]] = None
    security: Optional[List[Coding]] = None
    tag: Optional[List[Coding]] = None


class Narrative(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    status: Annotated[
        StrictStr,
        Field(
            description="The status of the narrative &ndash; whether it's entirely generated (from just the defined data or the extensions too), or whether a human authored it and it may contain additional data."
        ),
    ]
    div: Annotated[
        StrictStr,
        Field(
            description="The actual narrative content, a stripped down version of XHTML."
        ),
    ]


class DocumentId(BaseModel):
    __root__: StrictStr


class RequestPathParams(BaseModel):
    id: DocumentId


class RequestQuerySubject(BaseModel):
    __root__: Annotated[
        StrictStr, Field(example="https://fhir.nhs.uk/Id/nhs-number|4409815415")
    ]


class RequestQueryType(BaseModel):
    __root__: Annotated[StrictStr, Field(example="http://snomed.info/sct|736253002")]


class NextPageToken(BaseModel):
    __root__: StrictStr


class RequestHeaderOdsCode(BaseModel):
    __root__: StrictStr


class RequestHeaderRequestId(BaseModel):
    __root__: Annotated[
        StrictStr, Field(example="60E0B220-8136-4CA5-AE46-1D97EF59D068")
    ]


class RequestHeaderCorrelationId(BaseModel):
    __root__: Annotated[
        StrictStr, Field(example="11C46F5F-CDEF-4865-94B2-0EE0EDCC26DA")
    ]


class DocumentReferenceContent(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    attachment: Annotated[
        Attachment,
        Field(
            description="The document or URL of the document along with critical metadata to prove content has integrity."
        ),
    ]
    format: Annotated[
        Optional[Coding],
        Field(
            description="An identifier of the document encoding, structure, and template that the document conforms to beyond the base format indicated in the mimeType."
        ),
    ] = None


class CodeableConcept(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    coding: Optional[List[Coding]] = None
    text: Annotated[
        Optional[StrictStr],
        Field(
            description="A human language representation of the concept as seen/selected/uttered by the user who entered the data and/or which represents the intended meaning of the user."
        ),
    ] = None


class RequestHeader(BaseModel):
    odsCode: RequestHeaderOdsCode


class RequestParams(BaseModel):
    subject_identifier: Annotated[
        Optional[RequestQuerySubject], Field(alias="subject:identifier")
    ] = None
    type: Optional[RequestQueryType] = None
    next_page_token: Annotated[
        Optional[NextPageToken], Field(alias="next-page-token")
    ] = None


class OperationOutcomeIssue(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    severity: Annotated[
        StrictStr,
        Field(
            description="Indicates whether the issue indicates a variation from successful processing."
        ),
    ]
    code: Annotated[
        StrictStr,
        Field(
            description="Describes the type of the issue. The system that creates an OperationOutcome SHALL choose the most applicable code from the IssueType value set, and may additional provide its own code for the error in the details element."
        ),
    ]
    details: Annotated[
        Optional[CodeableConcept],
        Field(
            description="Additional details about the error. This may be a text description of the error or a system code that identifies the error."
        ),
    ] = None
    diagnostics: Annotated[
        Optional[StrictStr],
        Field(description="Additional diagnostic information about the issue."),
    ] = None
    location: Optional[List[LocationItem]] = None
    expression: Optional[List[ExpressionItem]] = None


class OperationOutcome(BaseModel):
    resourceType: Literal["OperationOutcome"]
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="The logical id of the resource, as used in the URL for the resource. Once assigned, this value never changes."
        ),
    ] = None
    meta: Annotated[
        Optional[Meta],
        Field(
            description="The metadata about the resource. This is content that is maintained by the infrastructure. Changes to the content might not always be associated with version changes to the resource."
        ),
    ] = None
    implicitRules: Annotated[
        Optional[StrictStr],
        Field(
            description="A reference to a set of rules that were followed when the resource was constructed, and which must be understood when processing the content. Often, this is a reference to an implementation guide that defines the special rules along with other profiles etc."
        ),
    ] = None
    language: Annotated[
        Optional[StrictStr],
        Field(description="The base language in which the resource is written."),
    ] = None
    text: Annotated[
        Optional[Narrative],
        Field(
            description='A human&ndash;readable narrative that contains a summary of the resource and can be used to represent the content of the resource to a human. The narrative need not encode all the structured data, but is required to contain sufficient detail to make it "clinically safe" for a human to just read the narrative. Resource definitions may define what content should be represented in the narrative to ensure clinical safety.'
        ),
    ] = None
    issue: Annotated[List[OperationOutcomeIssue], Field(min_items=1)]


class DocumentReference(BaseModel):
    resourceType: Literal["DocumentReference"]
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="The logical id of the resource, as used in the URL for the resource. Once assigned, this value never changes."
        ),
    ] = None
    meta: Annotated[
        Optional[Meta],
        Field(
            description="The metadata about the resource. This is content that is maintained by the infrastructure. Changes to the content might not always be associated with version changes to the resource."
        ),
    ] = None
    implicitRules: Annotated[
        Optional[StrictStr],
        Field(
            description="A reference to a set of rules that were followed when the resource was constructed, and which must be understood when processing the content. Often, this is a reference to an implementation guide that defines the special rules along with other profiles etc."
        ),
    ] = None
    language: Annotated[
        Optional[StrictStr],
        Field(description="The base language in which the resource is written."),
    ] = None
    text: Annotated[
        Optional[Narrative],
        Field(
            description='A human&ndash;readable narrative that contains a summary of the resource and can be used to represent the content of the resource to a human. The narrative need not encode all the structured data, but is required to contain sufficient detail to make it "clinically safe" for a human to just read the narrative. Resource definitions may define what content should be represented in the narrative to ensure clinical safety.'
        ),
    ] = None
    masterIdentifier: Annotated[
        Optional[Identifier],
        Field(
            description="Document identifier as assigned by the source of the document. This identifier is specific to this version of the document. This unique identifier may be used elsewhere to identify this version of the document."
        ),
    ] = None
    identifier: Optional[List[Identifier]] = None
    status: Annotated[
        StrictStr, Field(description="The status of this document reference.")
    ]
    docStatus: Annotated[
        Optional[StrictStr], Field(description="The status of the underlying document.")
    ] = None
    type: Annotated[
        Optional[CodeableConcept],
        Field(
            description="Specifies the particular kind of document referenced  (e.g. History and Physical, Discharge Summary, Progress Note). This usually equates to the purpose of making the document referenced."
        ),
    ] = None
    category: Optional[List[CodeableConcept]] = None
    subject: Annotated[
        Optional[Reference],
        Field(
            description="Who or what the document is about. The document can be about a person, (patient or healthcare practitioner), a device (e.g. a machine) or even a group of subjects (such as a document about a herd of farm animals, or a set of patients that share a common exposure)."
        ),
    ] = None
    date: Annotated[
        Optional[StrictStr],
        Field(description="When the document reference was created."),
    ] = None
    author: Optional[List[Reference]] = None
    authenticator: Annotated[
        Optional[Reference],
        Field(
            description="Which person or organization authenticates that this document is valid."
        ),
    ] = None
    custodian: Annotated[
        Optional[Reference],
        Field(
            description="Identifies the organization or group who is responsible for ongoing maintenance of and access to the document."
        ),
    ] = None
    relatesTo: Optional[List[DocumentReferenceRelatesTo]] = None
    description: Annotated[
        Optional[StrictStr],
        Field(description="Human&ndash;readable description of the source document."),
    ] = None
    securityLabel: Optional[List[CodeableConcept]] = None
    content: Annotated[List[DocumentReferenceContent], Field(min_items=1)]
    context: Annotated[
        Optional[DocumentReferenceContext],
        Field(description="The clinical context in which the document was prepared."),
    ] = None


class Bundle(BaseModel):
    resourceType: Literal["Bundle"]
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="The logical id of the resource, as used in the URL for the resource. Once assigned, this value never changes."
        ),
    ] = None
    meta: Annotated[
        Optional[Meta],
        Field(
            description="The metadata about the resource. This is content that is maintained by the infrastructure. Changes to the content might not always be associated with version changes to the resource."
        ),
    ] = None
    implicitRules: Annotated[
        Optional[StrictStr],
        Field(
            description="A reference to a set of rules that were followed when the resource was constructed, and which must be understood when processing the content. Often, this is a reference to an implementation guide that defines the special rules along with other profiles etc."
        ),
    ] = None
    language: Annotated[
        Optional[StrictStr],
        Field(description="The base language in which the resource is written."),
    ] = None
    identifier: Annotated[
        Optional[Identifier],
        Field(
            description="A persistent identifier for the bundle that won't change as a bundle is copied from server to server."
        ),
    ] = None
    type: Annotated[
        StrictStr,
        Field(
            description="Indicates the purpose of this bundle &ndash; how it is intended to be used."
        ),
    ]
    timestamp: Annotated[
        Optional[StrictStr],
        Field(
            description="The date/time that the bundle was assembled &ndash; i.e. when the resources were placed in the bundle."
        ),
    ] = None
    total: Annotated[
        Optional[StrictInt],
        Field(
            description="If a set of search matches, this is the total number of entries of type 'match' across all pages in the search.  It does not include search.mode = 'include' or 'outcome' entries and it does not provide a count of the number of entries in the Bundle."
        ),
    ] = None
    link: Optional[List[BundleLink]] = None
    entry: Optional[List[BundleEntry]] = None
    signature: Annotated[
        Optional[Signature],
        Field(
            description="Digital Signature &ndash; base64 encoded. XML&ndash;DSig or a JWT."
        ),
    ] = None


class BundleEntry(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    link: Optional[List[BundleLink]] = None
    fullUrl: Annotated[
        Optional[StrictStr],
        Field(
            description="The Absolute URL for the resource.  The fullUrl SHALL NOT disagree with the id in the resource &ndash; i.e. if the fullUrl is not a urn:uuid, the URL shall be version&ndash;independent URL consistent with the Resource.id. The fullUrl is a version independent reference to the resource. The fullUrl element SHALL have a value except that: \n* fullUrl can be empty on a POST (although it does not need to when specifying a temporary id for reference in the bundle)\n* Results from operations might involve resources that are not identified."
        ),
    ] = None
    resource: Annotated[
        Optional[DocumentReference],
        Field(
            description="The Resource for the entry. The purpose/meaning of the resource is determined by the Bundle.type."
        ),
    ] = None
    search: Annotated[
        Optional[BundleEntrySearch],
        Field(
            description="Information about the search process that lead to the creation of this entry."
        ),
    ] = None
    request: Annotated[
        Optional[BundleEntryRequest],
        Field(
            description="Additional information about how this entry should be processed as part of a transaction or batch.  For history, it shows how the entry was processed to create the version contained in the entry."
        ),
    ] = None
    response: Annotated[
        Optional[BundleEntryResponse],
        Field(
            description="Indicates the results of processing the corresponding 'request' entry in the batch or transaction being responded to or what the results of an operation where when returning history."
        ),
    ] = None


class BundleEntryResponse(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    status: Annotated[
        StrictStr,
        Field(
            description="The status code returned by processing this entry. The status SHALL start with a 3 digit HTTP code (e.g. 404) and may contain the standard HTTP description associated with the status code."
        ),
    ]
    location: Annotated[
        Optional[StrictStr],
        Field(
            description="The location header created by processing this operation, populated if the operation returns a location."
        ),
    ] = None
    etag: Annotated[
        Optional[StrictStr],
        Field(
            description="The Etag for the resource, if the operation for the entry produced a versioned resource (see [Resource Metadata and Versioning](http.html#versioning) and [Managing Resource Contention](http.html#concurrency))."
        ),
    ] = None
    lastModified: Annotated[
        Optional[StrictStr],
        Field(
            description="The date/time that the resource was modified on the server."
        ),
    ] = None
    outcome: Annotated[
        Optional[DocumentReference],
        Field(
            description="An OperationOutcome containing hints and warnings produced as part of processing this entry in a batch or transaction."
        ),
    ] = None


class DocumentReferenceContext(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    encounter: Optional[List[Reference]] = None
    event: Optional[List[CodeableConcept]] = None
    period: Annotated[
        Optional[Period],
        Field(
            description="The time period over which the service that is described by the document was provided."
        ),
    ] = None
    facilityType: Annotated[
        Optional[CodeableConcept],
        Field(description="The kind of facility where the patient was seen."),
    ] = None
    practiceSetting: Annotated[
        Optional[CodeableConcept],
        Field(
            description="This property may convey specifics about the practice setting where the content was created, often reflecting the clinical specialty."
        ),
    ] = None
    sourcePatientInfo: Annotated[
        Optional[Reference],
        Field(
            description="The Patient Information as known when the document was published. May be a reference to a version specific, or contained."
        ),
    ] = None
    related: Optional[List[Reference]] = None


class DocumentReferenceRelatesTo(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    code: Annotated[
        StrictStr,
        Field(
            description="The type of relationship that this document has with anther document."
        ),
    ]
    target: Annotated[
        Reference, Field(description="The target document of this relationship.")
    ]


class Identifier(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    use: Annotated[
        Optional[StrictStr], Field(description="The purpose of this identifier.")
    ] = None
    type: Annotated[
        Optional[CodeableConcept],
        Field(
            description="A coded type for the identifier that can be used to determine which identifier to use for a specific purpose."
        ),
    ] = None
    system: Annotated[
        Optional[StrictStr],
        Field(
            description="Establishes the namespace for the value &ndash; that is, a URL that describes a set values that are unique."
        ),
    ] = None
    value: Annotated[
        Optional[StrictStr],
        Field(
            description="The portion of the identifier typically relevant to the user and which is unique within the context of the system."
        ),
    ] = None
    period: Annotated[
        Optional[Period],
        Field(description="Time period during which identifier is/was valid for use."),
    ] = None
    assigner: Annotated[
        Optional[Reference],
        Field(description="Organization that issued/manages the identifier."),
    ] = None


class Reference(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    reference: Annotated[
        Optional[StrictStr],
        Field(
            description="A reference to a location at which the other resource is found. The reference may be a relative reference, in which case it is relative to the service base URL, or an absolute URL that resolves to the location where the resource is found. The reference may be version specific or not. If the reference is not to a FHIR RESTful server, then it should be assumed to be version specific. Internal fragment references (start with '#') refer to contained resources."
        ),
    ] = None
    type: Annotated[
        Optional[StrictStr],
        Field(
            description='The expected type of the target of the reference. If both Reference.type and Reference.reference are populated and Reference.reference is a FHIR URL, both SHALL be consistent.\nThe type is the Canonical URL of Resource Definition that is the type this reference refers to. References are URLs that are relative to http://hl7.org/fhir/StructureDefinition/ e.g. "Patient" is a reference to http://hl7.org/fhir/StructureDefinition/Patient. Absolute URLs are only allowed for logical models (and can only be used in references in logical models, not resources).'
        ),
    ] = None
    identifier: Annotated[
        Optional[Identifier],
        Field(
            description="An identifier for the target resource. This is used when there is no way to reference the other resource directly, either because the entity it represents is not available through a FHIR server, or because there is no way for the author of the resource to convert a known identifier to an actual location. There is no requirement that a Reference.identifier point to something that is actually exposed as a FHIR instance, but it SHALL point to a business concept that would be expected to be exposed as a FHIR instance, and that instance would need to be of a FHIR resource type allowed by the reference."
        ),
    ] = None
    display: Annotated[
        Optional[StrictStr],
        Field(
            description="Plain text narrative that identifies the resource in addition to the resource reference."
        ),
    ] = None


class Signature(BaseModel):
    id: Annotated[
        Optional[StrictStr],
        Field(
            description="Unique id for the element within a resource (for internal references). This may be any string value that does not contain spaces."
        ),
    ] = None
    type: Annotated[List[Coding], Field(min_items=1)]
    when: Annotated[
        StrictStr, Field(description="When the digital signature was signed.")
    ]
    who: Annotated[
        Reference,
        Field(
            description="A reference to an application&ndash;usable description of the identity that signed  (e.g. the signature used their private key)."
        ),
    ]
    onBehalfOf: Annotated[
        Optional[Reference],
        Field(
            description="A reference to an application&ndash;usable description of the identity that is represented by the signature."
        ),
    ] = None
    targetFormat: Annotated[
        Optional[StrictStr],
        Field(
            description="A mime type that indicates the technical format of the target resources signed by the signature."
        ),
    ] = None
    sigFormat: Annotated[
        Optional[StrictStr],
        Field(
            description="A mime type that indicates the technical format of the signature. Important mime types are application/signature+xml for X ML DigSig, application/jose for JWS, and image/* for a graphical image of a signature, etc."
        ),
    ] = None
    data: Annotated[
        Optional[StrictStr],
        Field(
            description="The base64 encoding of the Signature content. When signature is not recorded electronically this element would be empty."
        ),
    ] = None


DocumentReference.update_forward_refs()
Bundle.update_forward_refs()
BundleEntry.update_forward_refs()
DocumentReferenceContext.update_forward_refs()
DocumentReferenceRelatesTo.update_forward_refs()
Identifier.update_forward_refs()
