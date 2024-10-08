import json
from decimal import Decimal

from .models.feature_set import FeatureSet
from .utils.message import Message


class MonitorPoint:
    def __init__(self, feature_set: FeatureSet, desired_n_segments: int = 5):
        self.feature_set = feature_set
        self.desired_n_segments = desired_n_segments
        self.fid_shreve_map = []

        for feature in self.feature_set.featuresList:
            self.fid_shreve_map.append(feature.shreve)

    def run(self, log: Message) -> None:
        log.append("\n\nIniciando cálculo de SHARP")
        l_sharp = self.calculate_sharp(log)
        final_result = self.find_candidates(l_sharp, log)

        for sharp in final_result.keys():
            for feature_id in final_result[sharp]:
                self.feature_set.setFeatureClassification(
                    featureId=feature_id, sharp=sharp
                )

    def calculate_sharp(self, log: Message) -> list[Decimal]:
        Ma = Decimal(max(self.fid_shreve_map))
        log.append(f"Ordem da foz: {Ma}")
        l_sharp: list[Decimal] = []

        while len(l_sharp) != self.desired_n_segments:
            T = (Ma + 1) / 2
            l_sharp.append(T)
            Ma = T

        l_sharp.sort(reverse=True)
        log.append(f"Resultados SHARP:\n{l_sharp}")
        return l_sharp

    def find_candidates(
        self, l_sharp: list[Decimal], log: Message
    ) -> dict[Decimal, list[int]]:
        final_result: dict[Decimal, list[int]] = {}
        for sharp in l_sharp:
            if not self._find_exact_matches(final_result, sharp):
                self._find_closest_matches(final_result, sharp)

        log.append(
            f"MonitorPoint - Resultado final:\n{json.dumps(final_result, indent=2)}"
        )
        return final_result

    def _find_closest_matches(
        self, final_result: dict[Decimal, list[int]], sharp: Decimal
    ) -> None:
        rounded = round(sharp)
        found = False
        dif = 1
        while not found and dif < len(self.fid_shreve_map):
            for feature_id, shreve in enumerate(self.fid_shreve_map):
                if shreve == rounded - dif or shreve == rounded + dif:
                    found = True
                    if sharp not in final_result:
                        final_result[sharp] = [feature_id]
                    else:
                        final_result[sharp].append(feature_id)
            dif += 1

    def _find_exact_matches(
        self, final_result: dict[Decimal, list[int]], sharp: Decimal
    ) -> bool:
        rounded = round(sharp)
        found = False
        for feature_id, shreve in enumerate(self.fid_shreve_map):
            if shreve == rounded:
                found = True
                if sharp not in final_result:
                    final_result[sharp] = [feature_id]
                else:
                    final_result[sharp].append(feature_id)
        return found
