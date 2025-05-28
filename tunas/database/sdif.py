"""
Constants defined in the USA Swimming Standard Interchange Format (SDIF).
Most classes correspond to code tables defined in the SDIF specifications.
"""

import enum


class Organization(enum.Enum):
    """
    All organizations defined under the USA Swimming Standard Interchange Format (ORG Code 001).
    """

    USA_SWIMMING = "1"
    MASTERS = "2"
    NCAA = "3"
    NCAA_DIV_I = "4"
    NCAA_DIV_II = "5"
    NCAA_DIV_III = "6"
    YMCA = "7"
    FINA = "8"
    HIGH_SCHOOL = "9"


class LSC(enum.Enum):
    """
    All LSCs defined under the USA Swimming Standard Interchange Format (LSC Code 002).
    """

    ADIRONDACK = "AD"
    ALASKA = "AK"
    ALLEGHENY_MOUNTAIN = "AM"
    ARKANSAS = "AR"
    ARIZONA = "AZ"
    BORDER = "BD"
    SOUTHERN_CALIFORNIA = "CA"
    CENTRAL_CALIFORNIA = "CC"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    FLORIDA_GOLD_COAST = "FG"
    FLORIDA = "FL"
    GEORGIA = "GA"
    GULF = "GU"
    HAWAII = "HI"
    IOWA = "IA"
    INLAND_EMPIRE = "IE"
    ILLINOIS = "IL"
    INDIANA = "IN"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    LAKE_ERIE = "LE"
    MIDDLE_ATLANTIC = "MA"
    MARYLAND = "MD"
    MAINE = "ME"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    METROPOLITAN = "MR"
    MISSISSIPPI = "MS"
    MONTANA = "MT"
    MISSOURI_VALLEY = "MV"
    MIDWESTERN = "MW"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    NEW_ENGLAND = "NE"
    NIAGARA = "NI"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NORTH_TEXAS = "NT"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    OZARK = "OZ"
    PACIFIC = "PC"
    PACIFIC_NORTHWEST = "PN"
    POTOMAC_VALLEY = "PV"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA = "SD"
    SOUTHEASTERN = "SE"
    SAN_DIEGO_IMPERIAL = "SI"
    SIERRA_NEVADA = "SN"
    SNAKE_RIVER = "SR"
    SOUTH_TEXAS = "ST"
    UTAH = "UT"
    VIRGINIA = "VA"
    WISCONSIN = "WI"
    WEST_TEXAS = "WT"
    WEST_VIRGINIA = "WV"
    WYOMING = "WY"

    def __str__(self) -> str:
        return self.value


class Country(enum.Enum):
    """
    All countries defined under the USA Swimming Standard Interchange Format (COUNTRY
    Code 004). Includes citizenship distinctions Dual and Foreign which are defined
    in (CITIZEN Code 009)
    """

    AFGHANISTAN = "AFG"
    DUTCH_WEST_INDIES = "AHO"
    ALBANIA = "ALB"
    ALGERIA = "ALG"
    ANDORRA = "AND"
    ANGOLA = "ANG"
    ANTIGUA = "ANT"
    ARGENTINA = "ARG"
    ARMENIA = "ARM"
    ARUBA = "ARU"
    AMERICAN_SAMOA = "ASA"
    AUSTRALIA = "AUS"
    AUSTRIA = "AUT"
    AZERBAIJAN = "AZE"
    BAHAMAS = "BAH"
    BANGLADESH = "BAN"
    BARBADOS = "BAR"
    BELGIUM = "BEL"
    BENIN = "BEN"
    BERMUDA = "BER"
    BHUTAN = "BHU"
    BELIZE = "BIZ"
    BELARUS = "BLS"
    BOLIVIA = "BOL"
    BOTSWANA = "BOT"
    BRAZIL = "BRA"
    BAHRAIN = "BRN"
    BRUNEI = "BRU"
    BULGARIA = "BUL"
    BURKINA_FASO = "BUR"
    CENTRAL_AFRICAN_REPUBLIC = "CAF"
    CANADA = "CAN"
    CAYMAN_ISLANDS = "CAY"
    CONGO = "CGO"
    CHAD = "CHA"
    CHILE = "CHI"
    CHINA = "CHN"
    IVORY_COAST = "CIV"
    CAMEROON = "CMR"
    COOK_ISLANDS = "COK"
    COLUMBIA = "COL"
    COSTA_RICA = "CRC"
    CROATIA = "CRO"
    CUBA = "CUB"
    CYPRUS = "CYP"
    DENMARK = "DEN"
    DJIBOUTI = "DJI"
    DOMINICAN_REPUBLIC = "COM"
    ECUADOR = "ECU"
    EGYPT = "EGY"
    EL_SALVADOR = "ESA"
    SPAIN = "ESP"
    ESTONIA = "EST"
    ETHIOPIA = "ETH"
    FIJI = "FIJ"
    FINLAND = "FIN"
    FRANCE = "FRA"
    GABON = "GAB"
    GAMBIA = "GAM"
    GREAT_BRITAIN = "GBR"
    GERMANY = "GER"
    GEORGIA = "GEO"
    EQUATORIAL_GUINEA = "GEO"
    GHANA = "GHA"
    GREECE = "GRE"
    GRENADA = "GRN"
    GUATEMALA = "GUA"
    GUINEA = "GUI"
    GUAM = "GUM"
    GUYANA = "GUY"
    HAITI = "HAI"
    HONG_KONG = "HKG"
    HONDURAS = "HON"
    HUNGARY = "HUN"
    INDONESIA = "INA"
    INDIA = "IND"
    IRELAND = "IRL"
    IRAN = "IRI"
    IRAQ = "IRQ"
    ICELAND = "ISL"
    ISRAEL = "ISR"
    VIRGIN_ISLANDS = "ISV"
    ITALY = "ITA"
    BRITISH_VIRGIN_ISLANDS = "IVB"
    JAMAICA = "JAM"
    JORDAN = "JOR"
    JAPAN = "JPN"
    KENYA = "KEN"
    KRYGHYZSTAN = "KGZ"
    SOUTH_KOREA = "KOR"
    SAUDI_ARABIA = "KSA"
    KUWAIT = "KUW"
    KAZAKHSTAN = "KZK"
    LAOS = "LAO"
    LATVIA = "LAT"
    LIBYA = "LBA"
    LIBERIA = "LBR"
    LESOTHO = "LES"
    LEBANON = "LIB"
    LIECHTENSTEIN = "LIE"
    LITHUANIA = "LIT"
    LUXEMBOURG = "LUX"
    MADAGASCAR = "MAD"
    MALAYSIA = "MAS"
    MOROCCO = "MAR"
    MALAWI = "MAW"
    MALDIVES = "MDV"
    MEXICO = "MEX"
    MONGOLIA = "MGL"
    MOLDOVA = "MLD"
    MALI = "MLI"
    MALTA = "MLT"
    MONACO = "MON"
    MOZAMBIQUE = "MOZ"
    MAURITIUS = "MRI"
    MAURITANIA = "MTN"
    MYANMAR = "MYA"
    NAMIBIA = "NAM"
    NICARAGUA = "NCA"
    NETHERLANDS = "NED"
    NEPAL = "NEP"
    NIGER = "NIG"
    NIGERIA = "NGR"
    NORWAY = "NOR"
    NEW_ZEALAND = "NZL"
    OMAN = "OMA"
    PAKISTAN = "PAK"
    PANAMA = "PAN"
    PARAGUAY = "PAR"
    PERU = "PER"
    PHILIPPINES = "PHI"
    PAPAU_NEW_GUINEA = "PNG"
    POLAND = "POL"
    PORTUGAL = "POR"
    NORTH_KOREA = "PRK"
    PUERTO_RICO = "PUR"
    QATAR = "QAT"
    ROMANIA = "ROM"
    SOUTH_AFRICA = "RSA"
    RUSSIA = "RUS"
    RWANDA = "RWA"
    WESTERN_SAMOA = "SAM"
    SENEGAL = "SEN"
    SEYCHELLES = "SEY"
    SINGAPORE = "SIN"
    SIERRA_LEONE = "SLE"
    SLOVENIA = "SLO"
    SAN_MARINO = "SMR"
    SOLOMON_ISLANDS = "SOL"
    SOMALIA = "SOM"
    SRI_LANKA = "SRI"
    SUDAN = "SUD"
    SWITZERLAND = "SUI"
    SURINAM = "SUR"
    SWEDEN = "SWE"
    SWAZILAND = "SWZ"
    TANZANIA = "TAN"
    CZECHOSLOVAKIA = "TCH"
    TONGA = "TGA"
    THAILAND = "THA"
    TADJIKISTAN = "TJK"
    TOGO = "TOG"
    TAIWAN = "TPE"
    TRINIDAD_TOBAGO = "TRI"
    TUNISIA = "TUN"
    TURKEY = "TUR"
    UNITED_ARAB_EMIRATES = "UAE"
    UGANDA = "UGA"
    UKRAINE = "UKR"
    URUGUAY = "URU"
    UNITED_STATES = "USA"
    VANUATU = "VAN"
    VENEZUELA = "VEN"
    VIETNAM = "VIE"
    SAINT_VINCENT = "VIN"
    YEMEN = "YEM"
    YUGOSLAVIA = "YUG"
    ZAIRE = "ZAI"
    ZAMBIA = "ZAM"
    ZIMBABWE = "ZIM"
    DUAL = "2AL"
    FOREIGN = "FGN"


class MeetType(enum.Enum):
    """
    All meet types defined under the USA Swimming Standard Interchange Format (MEET Code 005).
    """

    INVITATIONAL = "1"
    REGIONAL = "2"
    LSC_CHAMPIONSHIP = "3"
    ZONE = "4"
    ZONE_CHAMPIONSHIP = "5"
    NATIONAL_CHAMPIONSHIP = "6"
    JUNIORS = "7"
    SENIORS = "8"
    DUAL = "9"
    TIME_TRIALS = "0"
    INTERNATIONAL = "A"
    OPEN = "B"
    LEAGUE = "C"


class Region(enum.Enum):
    """
    All regions defined under the USA Swimming Standard Interchange Format (REGION Code 007)
    """

    REGION_1 = "1"
    REGION_2 = "2"
    REGION_3 = "3"
    REGION_4 = "4"
    REGION_5 = "5"
    REGION_6 = "6"
    REGION_7 = "7"
    REGION_8 = "8"
    REGION_9 = "9"
    REGION_10 = "A"
    REGION_11 = "B"
    REGION_12 = "C"
    REGION_13 = "D"
    REGION_14 = "E"


class Sex(enum.Enum):
    """
    All sexes defined under the USA Swimming Standard Interchange Format (SEX Code 010
    and EVENT SEX Code 011).
    """

    MALE = "M"
    FEMALE = "F"
    MIXED = "X"

    def __str__(self) -> str:
        return self.value


class Stroke(enum.Enum):
    """
    All strokes defined under the USA Swimming Standard Interchange Format (STROKE Code 012).
    """

    FREESTYLE = "1"
    BACKSTROKE = "2"
    BREASTSTROKE = "3"
    BUTTERFLY = "4"
    INDIVIDUAL_MEDLEY = "5"
    FREESTYLE_RELAY = "6"
    MEDLEY_RELAY = "7"

    def __str__(self) -> str:
        match self:
            case Stroke.FREESTYLE:
                return "Free"
            case Stroke.BACKSTROKE:
                return "Back"
            case Stroke.BREASTSTROKE:
                return "Breast"
            case Stroke.BUTTERFLY:
                return "Fly"
            case Stroke.INDIVIDUAL_MEDLEY:
                return "IM"
            case Stroke.FREESTYLE_RELAY:
                return "Free Relay"
            case Stroke.MEDLEY_RELAY:
                return "Medley Relay"

    def short(self) -> str:
        """
        Short string representation of stroke.
        """
        match self:
            case Stroke.FREESTYLE:
                return "FR"
            case Stroke.BACKSTROKE:
                return "BK"
            case Stroke.BREASTSTROKE:
                return "BR"
            case Stroke.BUTTERFLY:
                return "FL"
            case Stroke.INDIVIDUAL_MEDLEY:
                return "IM"
            case Stroke.FREESTYLE_RELAY:
                return "FR-R"
            case Stroke.MEDLEY_RELAY:
                return "IM-R"


class Course(enum.Enum):
    """
    Event course. The USA Swimming Standard Interchange Format represents
    courses in two ways (COURSE Code 013). Here, we use the integer
    representation as the default and the character representation
    as the shortened string.
    """

    SCM = "1"
    SCY = "2"
    LCM = "3"

    def __str__(self) -> str:
        return self.name

    def short(self) -> str:
        """
        Short string representation of course.
        """
        match self:
            case Course.SCM:
                return "S"
            case Course.SCY:
                return "Y"
            case Course.LCM:
                return "L"


class EventTimeClass(enum.Enum):
    """
    Event time class. Follows convention used in the USA Swimming Standard
    Interchange Format (EVENT TIME CLASS Code 014)
    """

    NO_LOWER_LIMIT = "U"
    NO_UPPER_LIMIT = "O"
    NOVICE = "1"
    B_STANDARD = "2"
    BB_STANDARD = "P"
    A_STANDARD = "3"
    AA_STANDARD = "4"
    AAA_STANDARD = "5"
    AAAA_STANDARD = "6"
    JUNIOR_STANDARD = "J"
    SENIOR_STANDARD = "S"


class AttachStatus(enum.Enum):
    """
    All attachment statuses defined in the USA Swimming Standard Interchange Format
    (ATTACH Code 016)
    """

    ATTACHED = "A"
    UNATTACHED = "U"


class Session(enum.Enum):
    """
    Swim meet sessions. Follows convention used in USA Swimming Standard
    Interchange Format (PRELIMS/FINALS Code 019).
    """

    PRELIMS = "P"
    FINALS = "F"
    SWIM_OFFS = "S"

    def __str__(self) -> str:
        return self.value


class AgeGroup(enum.Enum):
    """
    Swimmer age group. Each age group is represented by a min and
    max age.
    """

    AG_10_u = (0, 10)
    AG_11_12 = (11, 12)
    AG_13_14 = (13, 14)
    AG_15_16 = (15, 16)
    AG_17_18 = (17, 18)
    AG_SENIOR = (13, 1000)

    def __str__(self) -> str:
        match self:
            case AgeGroup.AG_10_u:
                return "10&u"
            case AgeGroup.AG_SENIOR:
                return "senior"
            case _:
                return f"{self.get_min_age()}-{self.get_max_age()}"

    def get_min_age(self) -> int:
        return self.value[0]

    def get_max_age(self) -> int:
        return self.value[1]


class Event(enum.Enum):
    """
    Swim event. Each event is represented by a distance, stroke,
    and course.
    """

    FREE_25_SCY = (25, Stroke.FREESTYLE, Course.SCY)
    FREE_50_SCY = (50, Stroke.FREESTYLE, Course.SCY)
    FREE_100_SCY = (100, Stroke.FREESTYLE, Course.SCY)
    FREE_200_SCY = (200, Stroke.FREESTYLE, Course.SCY)
    FREE_400_SCY = (400, Stroke.FREESTYLE, Course.SCY)
    FREE_500_SCY = (500, Stroke.FREESTYLE, Course.SCY)
    FREE_800_SCY = (800, Stroke.FREESTYLE, Course.SCY)
    FREE_1000_SCY = (1000, Stroke.FREESTYLE, Course.SCY)
    FREE_1650_SCY = (1650, Stroke.FREESTYLE, Course.SCY)
    BACK_25_SCY = (25, Stroke.BACKSTROKE, Course.SCY)
    BACK_50_SCY = (50, Stroke.BACKSTROKE, Course.SCY)
    BACK_100_SCY = (100, Stroke.BACKSTROKE, Course.SCY)
    BACK_200_SCY = (200, Stroke.BACKSTROKE, Course.SCY)
    BREAST_25_SCY = (25, Stroke.BREASTSTROKE, Course.SCY)
    BREAST_50_SCY = (50, Stroke.BREASTSTROKE, Course.SCY)
    BREAST_100_SCY = (100, Stroke.BREASTSTROKE, Course.SCY)
    BREAST_200_SCY = (200, Stroke.BREASTSTROKE, Course.SCY)
    FLY_25_SCY = (25, Stroke.BUTTERFLY, Course.SCY)
    FLY_50_SCY = (50, Stroke.BUTTERFLY, Course.SCY)
    FLY_100_SCY = (100, Stroke.BUTTERFLY, Course.SCY)
    FLY_200_SCY = (200, Stroke.BUTTERFLY, Course.SCY)
    IM_100_SCY = (100, Stroke.INDIVIDUAL_MEDLEY, Course.SCY)
    IM_200_SCY = (200, Stroke.INDIVIDUAL_MEDLEY, Course.SCY)
    IM_400_SCY = (400, Stroke.INDIVIDUAL_MEDLEY, Course.SCY)
    FREE_25_SCM = (25, Stroke.FREESTYLE, Course.SCM)
    FREE_50_SCM = (50, Stroke.FREESTYLE, Course.SCM)
    FREE_100_SCM = (100, Stroke.FREESTYLE, Course.SCM)
    FREE_200_SCM = (200, Stroke.FREESTYLE, Course.SCM)
    FREE_400_SCM = (400, Stroke.FREESTYLE, Course.SCM)
    FREE_800_SCM = (800, Stroke.FREESTYLE, Course.SCM)
    FREE_1500_SCM = (1500, Stroke.FREESTYLE, Course.SCM)
    BACK_25_SCM = (25, Stroke.BACKSTROKE, Course.SCM)
    BACK_50_SCM = (50, Stroke.BACKSTROKE, Course.SCM)
    BACK_100_SCM = (100, Stroke.BACKSTROKE, Course.SCM)
    BACK_200_SCM = (200, Stroke.BACKSTROKE, Course.SCM)
    BREAST_25_SCM = (25, Stroke.BREASTSTROKE, Course.SCM)
    BREAST_50_SCM = (50, Stroke.BREASTSTROKE, Course.SCM)
    BREAST_100_SCM = (100, Stroke.BREASTSTROKE, Course.SCM)
    BREAST_200_SCM = (200, Stroke.BREASTSTROKE, Course.SCM)
    FLY_25_SCM = (25, Stroke.BUTTERFLY, Course.SCM)
    FLY_50_SCM = (50, Stroke.BUTTERFLY, Course.SCM)
    FLY_100_SCM = (100, Stroke.BUTTERFLY, Course.SCM)
    FLY_200_SCM = (200, Stroke.BUTTERFLY, Course.SCM)
    IM_100_SCM = (100, Stroke.INDIVIDUAL_MEDLEY, Course.SCM)
    IM_200_SCM = (200, Stroke.INDIVIDUAL_MEDLEY, Course.SCM)
    IM_400_SCM = (400, Stroke.INDIVIDUAL_MEDLEY, Course.SCM)
    FREE_50_LCM = (50, Stroke.FREESTYLE, Course.LCM)
    FREE_100_LCM = (100, Stroke.FREESTYLE, Course.LCM)
    FREE_200_LCM = (200, Stroke.FREESTYLE, Course.LCM)
    FREE_400_LCM = (400, Stroke.FREESTYLE, Course.LCM)
    FREE_800_LCM = (800, Stroke.FREESTYLE, Course.LCM)
    FREE_1500_LCM = (1500, Stroke.FREESTYLE, Course.LCM)
    BACK_50_LCM = (50, Stroke.BACKSTROKE, Course.LCM)
    BACK_100_LCM = (100, Stroke.BACKSTROKE, Course.LCM)
    BACK_200_LCM = (200, Stroke.BACKSTROKE, Course.LCM)
    BREAST_50_LCM = (50, Stroke.BREASTSTROKE, Course.LCM)
    BREAST_100_LCM = (100, Stroke.BREASTSTROKE, Course.LCM)
    BREAST_200_LCM = (200, Stroke.BREASTSTROKE, Course.LCM)
    FLY_50_LCM = (50, Stroke.BUTTERFLY, Course.LCM)
    FLY_100_LCM = (100, Stroke.BUTTERFLY, Course.LCM)
    FLY_200_LCM = (200, Stroke.BUTTERFLY, Course.LCM)
    IM_200_LCM = (200, Stroke.INDIVIDUAL_MEDLEY, Course.LCM)
    IM_400_LCM = (400, Stroke.INDIVIDUAL_MEDLEY, Course.LCM)

    def __str__(self) -> str:
        event_basic = f"{self.get_distance()} {self.get_stroke()}"
        return f"{event_basic: <10} {self.get_course()}"

    def get_distance(self) -> int:
        """
        Return distance of event.
        """
        return self.value[0]

    def get_stroke(self) -> Stroke:
        """
        Return stroke of event.
        """
        return self.value[1]

    def get_course(self) -> Course:
        """
        Return course of event.
        """
        return self.value[2]


class State(enum.Enum):
    """
    State encoding. Follows USPS state abbreviations.
    """

    ALABAMA = "AL"
    ALASKA = "AK"
    ARIZONA = "AZ"
    ARKANSAS = "AR"
    CALIFORNIA = "CA"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    DELAWARE = "DE"
    DISTRICT_OF_COLUMBIA = "DC"
    FLORIDA = "FL"
    GEORGIA = "GA"
    HAWAII = "HI"
    IDAHO = "ID"
    ILLINOIS = "IL"
    INDIANA = "IN"
    IOWA = "IA"
    KANSAS = "KS"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    MAINE = "ME"
    MARYLAND = "MD"
    MASSACHUSETTS = "MA"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    MISSISSIPPI = "MS"
    MISSOURI = "MO"
    MONTANA = "MT"
    NEBRASKA = "NE"
    NEVADA = "NV"
    NEW_HAMPSHIRE = "NH"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NEW_YORK = "NY"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    PENNSYLVANIA = "PA"
    PUERTO_RICO = "PR"
    RHODE_ISLAND = "RI"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA = "SD"
    TENNESSEE = "TN"
    TEXAS = "TX"
    UTAH = "UT"
    VERMONT = "VT"
    VIRGINIA = "VA"
    WASHINGTON = "WA"
    WEST_VIRGINIA = "WV"
    WISCONSIN = "WI"
    WYOMING = "WY"
