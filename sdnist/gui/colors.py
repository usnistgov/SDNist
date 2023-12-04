from sdnist.gui.helper.paths import PathType

from sdnist.gui.strs import *

part_2_back_color = "#253a66"
white_color = "#ffffff"
black_color = "#000000"
dark_grey = "#525250"
light_grey = "#787777"

back_color = "#1c2942"

metareport_clr = "#e86487"
report_clr = "#5f74c7"
archive_clr = "#e6774c"

main_theme_color = "#2f3d94"
# PATH TYPE COLORS
path_type_colors = {
    PathType.CSV: {
        NAME: "DEID CSV",
        PART_1: {
            BACK_COLOR: "#117d64",
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.JSON: {
        NAME: "METADATA JSON",
        PART_1: {
            BACK_COLOR: "#7a4fc4",
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.REPORT: {
        NAME: "REPORT",
        PART_1: {
            BACK_COLOR: report_clr,
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.METAREPORT: {
        NAME: "METAREPORT",
        PART_1: {
            BACK_COLOR: metareport_clr,
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.ARCHIVE: {
        NAME: "ARCHIVE",
        PART_1: {
            BACK_COLOR: archive_clr,
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.INDEX: {
        NAME: "INDEX CSV",
        PART_1: {
            BACK_COLOR: "#117d64",
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.DEID_DATA_DIR: {
        NAME: "DIRECTORY",
        PART_1: {
            BACK_COLOR: "#ccc856",
            TEXT_COLOR: dark_grey
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.REPORTS: {
        NAME: "REPORTS DIR",
        PART_1: {
            BACK_COLOR: report_clr,
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.METAREPORTS: {
        NAME: "METAREPORTS",
        PART_1: {
            BACK_COLOR: metareport_clr,
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
    PathType.ARCHIVES: {
        NAME: "ARCHIVES DIR",
        PART_1: {
            BACK_COLOR: archive_clr,
            TEXT_COLOR: white_color
        },
        PART_2: {
            BACK_COLOR: part_2_back_color,
            TEXT_COLOR: white_color
        }
    },
}

THM_WATER_POKEMON = 'water_pokemon'
THM_POKEMON_TGC = 'pokemon_tgc'


class Theme:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'water_pokemon')
        self.background = kwargs.get('background', '#107496')
        self.views = kwargs.get('views', '#114e67')


themes = {
    THM_WATER_POKEMON: Theme(
        name=THM_WATER_POKEMON,
        background='#107496',
        views='#114e67'
    ),
    THM_POKEMON_TGC: Theme(
        name=THM_POKEMON_TGC,
        background='#304160',
        views='#a8b8c8'
    ),
}
