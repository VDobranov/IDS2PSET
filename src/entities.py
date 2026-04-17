"""IFC entity constants and validation helpers."""

import re
from typing import Set, List

# Валидные IFC4 сущности (основные, используемые в IDS)
_VALID_IFC_ENTITIES: Set[str] = {
    "IFCPROJECT",
    "IFCSITE",
    "IFCBUILDING",
    "IFCBUILDINGSTOREY",
    "IFCSPATIALZONE",
    "IFCSPATIALELEMENT",
    "IFCSPATIALSTRUCTUREELEMENT",
    "IFCELEMENT",
    "IFCBUILDINGELEMENT",
    "IFCBUILDINGELEMENTPROXY",
    "IFCWALL",
    "IFCWALLSTANDARDCASE",
    "IFCSLAB",
    "IFCCOLUMN",
    "IFCBEAM",
    "IFCDOOR",
    "IFCWINDOW",
    "IFCROOF",
    "IFCSTAIR",
    "IFCSTAIRFLIGHT",
    "IFCRAMP",
    "IFCRAMPFLIGHT",
    "IFCCOVERING",
    "IFCPLATE",
    "IFCMEMBER",
    "IFCPILE",
    "IFCFOOTING",
    "IFCCHIMNEY",
    "IFCCURTAINWALL",
    "IFCSHADINGDEVICE",
    "IFCELEMENTASSEMBLY",
    "IFCRAILING",
    "IFCDISTRIBUTIONELEMENT",
    "IFCDISTRIBUTIONFLOWELEMENT",
    "IFCFLOWSEGMENT",
    "IFCFLOWCONTROLLER",
    "IFCFLOWFITTING",
    "IFCFLOWTERMINAL",
    "IFCFLOWSTORAGEDEVICE",
    "IFCFLOWTREATMENTDEVICE",
    "IFCFLOWMOVINGDEVICE",
    "IFCFLOWTERMINALELEMENT",
    "IFCAIRTERMINAL",
    "IFCAIRTOAIRHEATRECOVERY",
    "IFCAUDIOVISUALAPPLIANCE",
    "IFCBOILER",
    "IFCBUILDINGELEMENTPART",
    "IFCBURNER",
    "IFCCABLECARRIERFITTING",
    "IFCCABLECARRIERSEGMENT",
    "IFCCABLEFITTING",
    "IFCCABLESEGMENT",
    "IFCCHILLER",
    "IFCCOIL",
    "IFCCOLUMNSTANDARDCASE",
    "IFCCOMMUNICATIONSAPPLIANCE",
    "IFCCONDENSER",
    "IFCCONTROLLER",
    "IFCCOOLEDBEAM",
    "IFCCOOLINGTOWER",
    "IFCCOVERINGSTANDARDCASE",
    "IFCDAMPER",
    "IFCDISTRIBUTIONCHAMBERELEMENT",
    "IFCDUCTFITTING",
    "IFCDUCTSEGMENT",
    "IFCELECTRICAPPLIANCE",
    "IFCELECTRICDISTRIBUTIONBOARD",
    "IFCELECTRICFLOWSTORAGEDEVICE",
    "IFCELECTRICGENERATOR",
    "IFCELECTRICMOTOR",
    "IFCEVAPORATIVECOOLER",
    "IFCEVAPORATOR",
    "IFCFAN",
    "IFCFILTERTYPE",
    "IFCFIRESUPPRESSIONTERMINAL",
    "IFCFLOWMETER",
    "IFCINTERCEPTOR",
    "IFCJUNCTIONBOX",
    "IFCLAMP",
    "IFCLIGHTFIXTURE",
    "IFCMEDICALDEVICE",
    "IFCOUTLET",
    "IFCPIPEFITTING",
    "IFCPIPESEGMENT",
    "IFCPUMP",
    "IFCRADIATOR",
    "IFCRECTANGULARDUCTSEGMENT",
    "IFCSANITARYTERMINAL",
    "IFCSPACEHEATER",
    "IFCSTACKTERMINAL",
    "IFCSWITCHINGDEVICE",
    "IFCTANK",
    "IFCTRANSFORMER",
    "IFCTUBEBUNDLE",
    "IFCUNITARYCONTROLELEMENT",
    "IFCUNITARYEQUIPMENT",
    "IFCVALVE",
    "IFCVIBRATIONISOLATOR",
    "IFCWATERSTORE",
    "IFCWINDGENERATOR",
    "IFCBEAMSTANDARDCASE",
    "IFCFURNISHINGELEMENT",
    "IFCFURNITURE",
    "IFCSYSTEMFURNITUREELEMENT",
    "IFCANNOTATION",
    "IFCGRID",
    "IFCPORT",
    "IFCOPENINGELEMENT",
    "IFCOPENINGSTANDARDCASE",
    "IFCPROJECTIONELEMENT",
    "IFCVOIDINGFEATURE",
    "IFCGEOGRAPHICELEMENT",
    "IFCCIVILELEMENT",
    "IFCTRANSPORTELEMENT",
    "IFCVIBRATIONDAMPER",
    "IFCEXTERNALSPATIALELEMENT",
    "IFCEXTERNALSPATIALZONE",
    "IFCSPACE",
    "IFCZONE",
    "IFCFLOWINSTRUMENT",
}

# Regex-паттерны, указывающие на реальное регулярное выражение
# Одиночные скобки/точки не считаем — они могут быть в обычных названиях
_REGEX_PATTERNS = [
    re.compile(r"\.\*"),  # .*
    re.compile(r"\.\+"),  # .+
    re.compile(r"\[\^?"),  # [ или [^
    re.compile(r"\^"),  # ^
    re.compile(r"\$"),  # $
    re.compile(r"\{"),  # {
    re.compile(r"\|"),  # |
    re.compile(r"\\[dwsDWS]"),  # \d \w \s \D \W \S
    re.compile(r"[^\s]\+"),  # X+ (квантификатор)
    re.compile(r"[^\s]\?"),  # X? (квантификатор)
    re.compile(r"\(\?"),  # (?: (?= и т.д.
]


def is_valid_ifc_entity(entity: str) -> bool:
    """Check if entity name is valid IFC4 entity."""
    base_entity = entity.split("/")[0] if "/" in entity else entity
    return base_entity in _VALID_IFC_ENTITIES


def validate_entities(entities: List[str]) -> List[str]:
    """Validate entities against IFC4.

    Returns list of invalid entities.
    """
    invalid = []
    for entity in entities:
        if not is_valid_ifc_entity(entity):
            invalid.append(entity)
    return invalid


def is_regex_like(text: str) -> bool:
    """Check if text contains regex-like patterns."""
    if not text:
        return False
    return any(p.search(text) for p in _REGEX_PATTERNS)
