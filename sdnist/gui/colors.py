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
