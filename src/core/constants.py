# Binary score constants
class BinaryScore:
    YES = "yes"
    NO = "no"


# Route decision constants
class RouteDecision:
    WEB_SEARCH = "web_search"
    KG_RETRIEVAL = "kg_retrieval"
    LLM_INTERNAL = "llm_internal"
    QUERY_TRANSFORMATION = "query_transformation"
    ANSWER_GENERATION = "answer_generation"
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"
    NOT_SUPPORTED = "not_supported"
    SUPPORTED = "supported"


# Log messages
class LogMessages:
    ROUTE_QUESTION = "[..] ROUTE QUESTION"
    ROUTE_TO = "[..] ROUTE QUESTION TO {}"
    WEB_SEARCH = "[..] WEB SEARCH"
    KNOWLEDGE_GRAPH_RETRIEVAL = "[..] KNOWLEDGE GRAPH RETRIEVAL"
    LLM_INTERNAL_ANSWER = "[..] LLM INTERNAL ANSWER (OUT OF DOMAIN)"
    ANSWER_GENERATION = "[..] ANSWER GENERATION"
    CHECK_DOCUMENT_RELEVANCE = "[..] CHECK DOCUMENT RELEVANCE TO QUESTION"
    QUERY_TRANSFORMATION = "[..] QUERY TRANSFORMATION"
    ASSESS_GRADED_DOCUMENTS = "[..] ASSESS GRADED DOCUMENTS"
    CHECK_HALLUCINATIONS = "[..] CHECK HALLUCINATIONS"
    CHECK_ANSWER_QUALITY = "[..] CHECK ANSWER QUALITY"
    GRADE_RELEVANT = "[..][..] GRADE: {} CONTENT RELEVANT"
    GRADE_NOT_RELEVANT = "[..][..] GRADE: {} CONTENT NOT RELEVANT"
    ERROR_GRADING = "[..][..] ERROR GRADING {} CONTENT: {}"
    ERROR_IN = "[..][..] ERROR IN {}: {}"
    DECISION_ALL_DOCUMENTS_NOT_RELEVANT = (
        "[..][..] DECISION: ALL DOCUMENTS ARE NOT RELEVANT, TRANSFORM QUERY"
    )
    DECISION_GENERATE = "[..][..] DECISION: GENERATE"
    DECISION_GROUNDED = "[..][..] DECISION: GENERATION IS GROUNDED IN DOCUMENTS"
    DECISION_NOT_GROUNDED = (
        "[..][..] DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY"
    )
    DECISION_ADDRESSES_QUESTION = "[..][..] DECISION: GENERATION ADDRESSES QUESTION"
    DECISION_NOT_ADDRESSES_QUESTION = (
        "[..][..] DECISION: GENERATION DOES NOT ADDRESS QUESTION"
    )
    MAX_RETRIES_REACHED = "[..][..] MAX RETRIES REACHED: {}/{}. FALLING BACK TO {}"
    RETRY_COUNT_INFO = "[..][..] RETRY COUNT: {}/{}"


# Default configuration values
class Defaults:
    N_RETRIEVED_DOCUMENTS = 3
    N_WEB_SEARCHES = 3
    NODE_RETRIEVAL = True
    EDGE_RETRIEVAL = True
    EPISODE_RETRIEVAL = False
    COMMUNITY_RETRIEVAL = False
    MAX_COROUTINES = 1
    MAX_RETRY_COUNT = 3  # Maximum number of query transformation retries
    ENABLE_RETRIEVED_DOCUMENTS_GRADING = True  # Enable retrieved documents grading
    ENABLE_GENERATION_GRADING = True  # Enable hallucination and answer quality checking


# Document Mapping Information that get from indexing pipeline {document_id: document_name}
DOCUMENT_ID_TO_DOCUMENT_NAME = {
    "6c4f90ec65191d48b991b01cb105139308d36b0d400134cff4c9c63408046999": "PL-DR-DP-ED-09-หนอนเจาะเมล็ดทุเรียน.pdf",
    "4203f979eb1789487360c0656b9dd80414a8b00f6a971bb1565233ef46ae95ac": "PL-DR-DP-ED-06-เพลี้ยหอย.pdf",
    "fe83d4f4d14482a9501a64c49fd1a160bce5d96af683891c32b1c010a379bf0d": "PL-DR-DP-ED-08-มอดเจาะลำต้น.pdf",
    "59baa43037f040205432d4df5c2315444b821baa825e5235d60c4204c81af373": "PL-DR-DP-THE-03-โรคกิ่งแห้งของทุเรียนที่เกิดจากเชื้อรา Lasiodiplodia theobromae และการควบคุมโดยใช้สารเคมี.pdf",
    "d94352337082a77a96311e010cfa43415fe54aa95da69d373152ca9359ec5eeb": "DR-DP-ED-02-โรคทุเรียนและการป้องกันกำจัด.pdf",
    "69703df5fb2c5e4d4dea3bf22874dd58cff886fe4935efe97883ad7686ba412d": "DR-DP-ED-03-โรคของทุเรียน.pdf",
    "3f4e161dbadfb1f5d8b14ce91fb9cacc0df48c389bda25d238c078c6b4066f56": "PL-DR-DP-ED-05-เพลี้ยจักจั่นฝอยทุเรียน.pdf",
    "230268976351b593911f53c2b4975c8203d26ac1aba7268da865f1129caac9e8": "PL-DR-DP-THE-02-การใช้สารป้องกันกำจัดเชื้อราควบคุมโรครากเน่าโคนเน่าและโรคผลเน่าหลังการเก็บเกี่.pdf",
    "d714aecf19cdb3bbfaa0c98e2ae0b134307e05856e526b0bd8b00fbb97b783b9": "DR-DP-ED-01-แมลงไรศัตรูทุเรียน.pdf",
    "1f47acc157568428dead1fefd6be09ca8b6ab04fe98126a829873f2ecc360cf3": "PL-DR-DP-THE-07-โรคกิ่งแห้งทุเรียนสาเหตุจากเชื้อรา Fusarium solani และการควบคุมด้วยสารเคมีป้องกันกำจัดเชื.pdf",
    "2b6cb88eeaff89d06ef86c8af1b2731b2cdf6804cee051978e5e0624279784af": "PL-DR-DP-THE-06-การตอบสนองต่อสารเคมีกำจัดเชื้อราของเชื้อรา Trichoderma spp ที่แยกได้จากแปลงทุเรียนในจังหว.pdf",
    "28887fc7cb382999bb1d0dfb743ca16875649553f8294be096acb7af2a27d14e": "PL-DR-DP-ED-07-ด้วงหนวดยาวเจาะลำต้น.pdf",
    "65740d481d34afb1c79ec5e67edd555cbb7781947359da6c00f9f34605e9cbcc": "PL-DR-DP-THE-05-ศักยภาพของเชื้อรา Trichoderma spp ที่แยกได้จากดินจังหวัดจันทบุรี ชุมพรและตราด ต่อการควบคุมเ.pdf",
    "ab3f854b612cc512f541cbbead31d7a83c858c2935666f11230ee4e62546cf0e": "PL-DR-DP-THE-04-ความหลากหลายทางพันธุกรรมและกลไกความต้านทานต่อสารเคมี metalaxyl ในเชื้อ Phytophthora palmivora สาเหตุโ.pdf",
    "ff5655b31bd4631ffca78f15434bc34da5c2579f3c2b97ac68a2b41a752a868f": "PL-DR-DP-ED-04-เพลี้ยไก่แจ้ทุเรียน.pdf",
    "654de101070de9d194a4e3b559d902ed1ab8f5e41689af5944b618cd8d74b6dc": "PL-DR-DP-THE-01-ความหลากหลายของเชื้อรา Phomopsis spp. สาเหตุโรคทุเรียนและการต้านทานสารเคมีป้องกันกำจัดเชื.pdf",
}
