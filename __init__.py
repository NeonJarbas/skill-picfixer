from pyvod import Collection, Media
from os.path import join, dirname, basename
from ovos_workshop.frameworks.playback import CommonPlayMediaType, CommonPlayPlaybackType, \
    CommonPlayMatchConfidence
from ovos_workshop.skills.video_collection import VideoCollectionSkill
from mycroft.skills.core import intent_file_handler


class PicFixerSkill(VideoCollectionSkill):

    def __init__(self):
        super().__init__("PicFixer")
        self.supported_media = [CommonPlayMediaType.GENERIC,
                                CommonPlayMediaType.MOVIE,
                                CommonPlayMediaType.VIDEO]
        self.message_namespace = basename(dirname(__file__)) + ".jarbasskills"
        # load video catalog
        path = join(dirname(__file__), "res", "feature_films_picfixer.jsondb")
        logo = join(dirname(__file__), "res", "picfixer.png")
        self.media_collection = Collection("feature_films_picfixer", logo=logo, db_path=path)
        self.default_image = join(dirname(__file__), "ui", "picfixer.png")
        self.skill_logo = join(dirname(__file__), "ui", "picfixer.png")
        self.skill_icon = join(dirname(__file__), "ui", "picfixer.png")
        self.default_bg = logo
        self.media_type = CommonPlayMediaType.MOVIE
        self.playback_type = CommonPlayPlaybackType.GUI

    # voice interaction
    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # better common play
    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "picfixer")
        title = self.remove_voc(title, "movie")
        title = self.remove_voc(title, "play")
        title = self.remove_voc(title, "video")
        title = self.remove_voc(title, "scifi")
        title = self.remove_voc(title, "short")
        title = self.remove_voc(title, "horror")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join([w for w in title.split(" ") if w])  # remove extra spaces

    def match_media_type(self, phrase, media_type):
        score = 0
        if self.voc_match(phrase, "video") or media_type == CommonPlayMediaType.VIDEO:
            score += 5

        if self.voc_match(phrase, "movie") or media_type == CommonPlayMediaType.MOVIE:
            score += 10

        if self.voc_match(phrase, "old"):
            score += 10

        if self.voc_match(phrase, "public_domain"):
            score += 15

        if self.voc_match(phrase, "picfixer"):
            score += 50

        return score


def create_skill():
    return PicFixerSkill()

