from os.path import join, dirname

from json_database import JsonStorage

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class PicFixerSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.MOVIE, MediaType.BLACK_WHITE_MOVIE]
        # load video catalog
        path = join(dirname(__file__), "res", "feature_films_picfixer.jsondb")
        logo = join(dirname(__file__), "res", "picfixer.png")
        self.archive = {v["streams"][0]: v for v in JsonStorage(path)["feature_films_picfixer"] if v["streams"]}

        self.default_image = join(dirname(__file__), "ui", "picfixer.png")
        self.skill_logo = join(dirname(__file__), "ui", "picfixer.png")
        self.skill_icon = join(dirname(__file__), "ui", "picfixer.png")
        self.default_bg = logo
        super().__init__(*args, **kwargs)
        self.load_ocp_keywords()

    def load_ocp_keywords(self):
        title = []
        bw_movies = []
        silent_movies = []
        docus = []

        for url, data in self.archive.items():
            t = data["title"].split("|")[0].split("(")[0].split(" video")[0].split(" restored")[0].strip()
            if "documentaries" in [_.lower() for _ in data["tags"]]:
                t = t
                docus.append(t)
                if ":" in t:
                    t1, t2 = t.split(":", 1)
                    docus.append(t1.strip())
                    docus.append(t2.strip())
            elif data.get("sound") in ["silent", "Silent, No Music"] or \
                    any(a in data["collection"] for a in ["silent_films"]) or \
                    any(a in data["tags"] for a in ["Silent", " silent", "silent"]):
                silent_movies.append(t)
                if ":" in t:
                    t1, t2 = t.split(":", 1)
                    silent_movies.append(t1.strip())
                    silent_movies.append(t2.strip())
            elif data.get("color") in ["b&w", "black & white", "black and white", "B&W"]:
                bw_movies.append(t)
                if ":" in t:
                    t1, t2 = t.split(":", 1)
                    bw_movies.append(t1.strip())
                    bw_movies.append(t2.strip())
            else:
                title.append(t)
                if ":" in t:
                    t1, t2 = t.split(":", 1)
                    title.append(t1.strip())
                    title.append(t2.strip())

        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_name", title)
        self.register_ocp_keyword(MediaType.BLACK_WHITE_MOVIE,
                                  "bw_movie_name", bw_movies)
        self.register_ocp_keyword(MediaType.SILENT_MOVIE,
                                  "silent_movie_name", silent_movies)
        self.register_ocp_keyword(MediaType.DOCUMENTARY,
                                  "documentary_name", docus)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_streaming_provider",
                                  ["PicFixer",
                                   "Picfixer Feature Film Collection",
                                   "Pic Fixer"])

    def get_playlist(self, score=50, num_entries=25):
        pl = self.featured_media()[:num_entries]
        return {
            "match_confidence": score,
            "media_type": MediaType.MOVIE,
            "playlist": pl,
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.default_image,
            "title": "Picfixer Feature Film Collection (Movie Playlist)",
            "author": "PicFixer"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = 15 if media_type in [MediaType.MOVIE, MediaType.BLACK_WHITE_MOVIE] else 0
        entities = self.ocp_voc_match(phrase)

        title = entities.get("movie_name")
        bw_title = entities.get("bw_movie_name")
        s_title = entities.get("silent_movie_name")
        skill = "movie_streaming_provider" in entities  # skill matched

        base_score += 30 * len(entities)

        if title or bw_title or s_title:
            candidates = self.archive.values()
            media_type = MediaType.MOVIE
            if title:
                base_score += 20
                candidates = [video for video in self.archive.values()
                              if title.lower() in video["title"].lower()]
            elif bw_title:
                media_type = MediaType.BLACK_WHITE_MOVIE
                base_score += 10
                candidates = [video for video in self.archive.values()
                              if bw_title.lower() in video["title"].lower()]
            elif s_title:
                media_type = MediaType.SILENT_MOVIE
                base_score += 10
                candidates = [video for video in self.archive.values()
                              if s_title.lower() in video["title"].lower()]

            for video in candidates:
                yield {
                    "title": video["title"],
                    "match_confidence": min(100, base_score),
                    "media_type": media_type,
                    "uri": video["streams"][0],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["images"][0] if video["images"] else self.default_image
                }

        if skill:
            yield self.get_playlist()

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": video["streams"][0],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": self.default_bg,
            "skill_id": self.skill_id
        } for video in self.archive.values()]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = PicFixerSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.search_db("play TEENAGE ZOMBIES", MediaType.BLACK_WHITE_MOVIE):
        print(r)
        # {'title': 'TEENAGE ZOMBIES video quality upgrade', 'match_confidence': 55, 'media_type': <MediaType.BLACK_WHITE_MOVIE: 20>, 'uri': 'https://archive.org/download/TeenageZombiesVideoQualityUpgrade/TeenageZombiesVideoQualityUpgrade.ogv', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-picfixer/ui/picfixer.png'}
