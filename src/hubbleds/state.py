import dataclasses
from cosmicds.state import GLOBAL_STATE, BaseState
from solara import Reactive
from glue.core import Data
from glue.core.data_factories import load_data
from pathlib import Path
from hubbleds.decorators import computed_property

# from glue.config import settings as glue_settings
# glue_settings.BACKGROUND_COLOR = 'white'
# glue_settings.FOREGROUND_COLOR= 'black'

from typing import Optional, Callable, Any, Tuple, List

from .data_management import HUBBLE_1929_DATA_LABEL, HUBBLE_KEY_DATA_LABEL
from .tools import *
from .free_response import *  # imports FreeResponse, fr_init_response, fr_response


@dataclasses.dataclass
class MCScore:
    tag: str = dataclasses.field(init=True)
    _score_dict: Reactive[dict[str, int]] = dataclasses.field(
        default_factory=lambda: Reactive({})
    )

    def update(self, score, choice, tries, wrong_attempts):
        print("updating", self.tag, score, choice, tries, wrong_attempts)
        self._score_dict.set(
            {
                "score": score,
                "choice": choice,
                "tries": tries,
                "wrong_attempts": wrong_attempts,
            }
        )

    def toJSON(self):
        return {
            "tag": self.tag,
            "score": self._score_dict.value.get("score", None),
            "choice": self._score_dict.value.get("choice", None),
            "tries": self._score_dict.value.get("tries", 0),
            "wrong_attempts": self._score_dict.value.get("wrong_attempts", 0),
        }

    def __repr__(self):
        return f"MCScore({self.toJSON()})"

    @computed_property
    def completed(self):
        return self._score_dict.value.get("score", None) is not None


@dataclasses.dataclass
class LocalState(BaseState):
    debug_mode: Reactive[bool] = dataclasses.field(default=Reactive(False))
    title: Reactive[str] = dataclasses.field(default=Reactive("Hubble's Law"))
    stages: Reactive[list] = dataclasses.field(default=Reactive([]))
    measurements: Reactive[dict] = dataclasses.field(default=Reactive({}))
    calculations: Reactive[dict] = dataclasses.field(default=Reactive({}))
    validation_failure_counts: Reactive[dict] = dataclasses.field(default=Reactive({}))
    has_best_fit_galaxy: Reactive[bool] = dataclasses.field(default=Reactive(False))
    enough_students_ready: Reactive[bool] = dataclasses.field(default=Reactive(False))
    started: Reactive[bool] = dataclasses.field(default=Reactive(False))
    class_data_students: Reactive[list] = dataclasses.field(default=Reactive([]))
    class_data_info: Reactive[dict] = dataclasses.field(default=Reactive({}))
    mc_scoring: Reactive[dict[str, MCScore]] = dataclasses.field(default=Reactive({}))
    free_responses: FreeResponseDict = dataclasses.field(default_factory=FreeResponseDict)

    def question_completed(self, qtag: str):
        if qtag in self.mc_scoring.value:
            return self.mc_scoring.value[qtag].completed().value  # type: ignore
        return False


LOCAL_STATE = LocalState()

# add a csv file to the data collection


def add_link(from_dc_name, from_att, to_dc_name, to_att):
    if isinstance(from_dc_name, Data):
        from_dc = from_dc_name
    else:
        from_dc = GLOBAL_STATE.data_collection[from_dc_name]
    
    if isinstance(to_dc_name, Data):
        to_dc = to_dc_name
    else:
        to_dc = GLOBAL_STATE.data_collection[to_dc_name]
    GLOBAL_STATE._glue_app.add_link(from_dc, from_att, to_dc, to_att)


data_dir = Path(__file__).parent / "data"

try:
    GLOBAL_STATE.data_collection.append(
        load_data(data_dir / f"{HUBBLE_KEY_DATA_LABEL}.csv")
    )
    GLOBAL_STATE.data_collection.append(
        load_data(data_dir / f"{HUBBLE_1929_DATA_LABEL}.csv")
    )

    add_link(
        HUBBLE_1929_DATA_LABEL,
        "Distance (Mpc)",
        HUBBLE_KEY_DATA_LABEL,
        "Distance (Mpc)",
    )
    add_link(
        HUBBLE_1929_DATA_LABEL,
        "Tweaked Velocity (km/s)",
        HUBBLE_KEY_DATA_LABEL,
        "Velocity (km/s)",
    )
except:
    print("Data already loaded into Glue.")


# create handlers for mc_radiogroup
def on_init_response(
    local_state: LocalState, tag: str, callback: Optional[Callable] = None
):
    print("onInitResponse")
    # print(tag not in component_state.mc_scoring.value.keys())
    if tag not in local_state.mc_scoring.value.keys():
        print("adding tag", tag)
        mc_scoring = local_state.mc_scoring.value
        print(MCScore(tag=tag))
        mc_scoring[tag] = MCScore(tag=tag)
        print(mc_scoring)
        local_state.mc_scoring.set(mc_scoring)
        if callback is not None:
            callback(mc_scoring)
    else:
        print("tag already exists")


def on_mc_score(local_state, data, callback: Optional[Callable] = None):
    print("on_mc_score")
    mc_scoring = local_state.mc_scoring.value
    mc_scoring[data["tag"]].update(
        data["score"], data["choice"], data["tries"], data["wrong_attempts"]
    )
    local_state.mc_scoring.set(mc_scoring)
    if callback is not None:
        callback(mc_scoring)


def mc_callback(event, local_state, callback: Optional[Callable] = None):
    # mc-initialize-callback returns data which is a string
    if event[0] == "mc-initialize-response":
        return on_init_response(
            local_state=local_state, tag=event[1], callback=callback
        )
    # mc-score event returns a data which is an mc-score dictionary
    elif event[0] == "mc-score":
        return on_mc_score(local_state=local_state, data=event[1], callback=callback)
    else:
        print(f"Unknown event in mc_callback: <<{event}>> ")


def mc_serialize_score(mc_score=None):
    if mc_score is None:
        return None
    return mc_score.toJSON()


def fr_callback(
    event: Tuple[str, dict[str, str]],
    local_state: LocalState,
    response_callback: Optional[Callable] = None,
):
    """
    Free Response callback function

    response_callback: Optional callback that takes in the response as an argument
        An example would be to set a value
    """
    print("fr_callback", event)
    if event[0] == "fr-initialize":
        # by using get_free_response in the Page, we can avoid separately
        # initializing the free response initialize_free_
        # response(local_state.free_responses, tag=event[1]['tag'])
        pass
    elif event[0] == "fr-update":
        update_free_response(
            local_state.free_responses,
            tag=event[1]["tag"],
            response=event[1]["response"],
        )
        if response_callback is not None:
            if (len(event) > 1) and ("response" in event[1]):
                response_callback(event[1]["response"])
    else:
        raise ValueError(f"Unknown event in fr_callback: <<{event}>> ")
