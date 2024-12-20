import functools

from ..utils.message import Message
from .segment import Segment


class RelationItem:
    def __init__(
        self,
        source: Segment,
        destination: Segment,
        relationType: int,
    ):
        self.source = source
        self.destination = destination
        self.relationType = relationType


class IndexItem:
    def __init__(self, featureId: int, value: int):
        self.featureId = featureId
        self.value = value


class Relation:
    def __init__(self, log: Message) -> None:
        self.log = log

        self.items: list[RelationItem] = []
        self.err: list[RelationItem] = []
        self.mouths: list[RelationItem] = []

        self.index: list[IndexItem] = []
        self.primaryIndex: list[IndexItem] = []

    def insert(
        self,
        source: Segment,
        destination: Segment,
        relation_type: int,
    ) -> None:
        new_item = RelationItem(source, destination, relation_type)
        target_list = self.items if relation_type == 0 else self.err

        if len(target_list) == 0:
            target_list.append(RelationItem(source, destination, relation_type))
            return

        start = 0
        end = len(target_list) - 1
        while start <= end:
            middle = (start + end) // 2
            item = target_list[middle]
            comp = self.comparePosition(new_item, item)

            if comp < 0:
                if start in (middle, end):
                    target_list.insert(middle, new_item)
                    return
                if start < middle:
                    end = middle - 1
                else:
                    target_list.insert(0, new_item)
                    return

            elif comp > 0:
                if middle == len(target_list) - 1:
                    target_list.append(new_item)
                    return
                if start == end:
                    target_list.insert(middle, new_item)
                    return
                start = middle + 1

            else:
                return

    def addMouth(self, drainage: Segment, boundary: Segment) -> None:
        # Garantindo que o primeiro argumento é da bacia.

        if drainage.setId == 0:
            drainage.isMouth = True
            item = RelationItem(drainage, boundary, 0)
        else:
            boundary.isMouth = True
            item = RelationItem(boundary, drainage, 0)

        # Garantindo que a foz não foi incluida antes.
        found = False
        for mouth in self.mouths:
            if item.source.featureId == mouth.source.featureId:
                found = True
                break

        if not found:
            # Inserindo em fozes.
            self.mouths.append(item)

    def addRelation(
        self, source: Segment, destination: Segment, relationType: int
    ) -> None:
        """
        Tipos de relação topológica:
        0 - Encosta
        1 - Toca
        2 - Intercepta
        """
        # Garantindo que o FID do primeiro segmento seja menor que o FID do segundo.
        if destination.featureId < source.featureId:
            source, destination = destination, source

        # Verificando se é relação entre foz e limite.
        # Só aceita relação topológica do tipo encosta entre foz e limite da bacia!
        if source.setId != destination.setId and relationType == 0:
            self.addMouth(source, destination)  # Versão 1.3!

        # Verificando se os segmenos são de feições diferentes da bacia.
        elif (
            source.featureId != destination.featureId
            and source.setId == 0
            and destination.setId == 0
        ):
            self.insert(source, destination, relationType)
        # Os segmentos da orígem e destino são da mesma feição. Não gravar!

    def findChildSegments(
        self, featureId: int, destFeatureId: int, siblings: list[Segment]
    ) -> list[Segment]:
        result = []
        # Obtendo o índice primário.
        primaryPos = self.findPrimaryIndex(featureId)

        if primaryPos >= 0:
            done = False
            while not done and primaryPos < len(self.index):
                # Obtendo o índice do evento.
                item = self.index[primaryPos]

                if item.featureId == featureId:
                    # Lendo evento.
                    eventItem = self.items[item.value]

                    relatedSegment = None
                    if (
                        eventItem.source.featureId == featureId
                        and eventItem.destination.featureId != destFeatureId
                    ):
                        relatedSegment = eventItem.destination
                    elif (
                        eventItem.destination.featureId == featureId
                        and eventItem.source.featureId != destFeatureId
                    ):
                        relatedSegment = eventItem.source

                    if relatedSegment:
                        isChild = True
                        for childSegment in siblings:
                            if relatedSegment.featureId == childSegment.featureId:
                                isChild = False
                        if isChild:
                            result.append(relatedSegment)

                    primaryPos += 1
                else:
                    done = True

        return list(result)

    def comparePosition(self, a: RelationItem, b: RelationItem) -> int:
        if all(
            [
                a.source.featureId == b.source.featureId,
                a.destination.featureId == b.destination.featureId,
                a.relationType == b.relationType,
            ]
        ):
            return 0
        if any(
            [
                a.source.featureId < b.source.featureId,
                (
                    a.source.featureId == b.source.featureId
                    and a.destination.featureId < b.destination.featureId
                ),
                (
                    a.source.featureId == b.source.featureId
                    and a.destination.featureId == b.destination.featureId
                    and a.relationType < b.relationType
                ),
            ]
        ):
            return -1
        if any(
            [
                a.source.featureId > b.source.featureId,
                (
                    a.source.featureId == b.source.featureId
                    and a.destination.featureId > b.destination.featureId
                ),
                (
                    a.source.featureId == b.source.featureId
                    and a.destination.featureId == b.destination.featureId
                    and a.relationType > b.relationType
                ),
            ]
        ):
            return 1
        return 0

    def findPrimaryIndex(self, featureId: int) -> int:
        for item in self.primaryIndex:
            if featureId == item.featureId:
                return item.value
        return -1

    def compareIndexItems(self, a: IndexItem, b: IndexItem) -> int:
        return (
            a.value - b.value
            if a.featureId == b.featureId
            else a.featureId - b.featureId
        )

    def buildIndexes(self) -> None:
        # Montando índice principal.
        self.index.clear()

        eventItem = None
        for i, eventItem in enumerate(self.items):
            # Verificando se são ocorrências de bacia.
            self.index.append(IndexItem(eventItem.source.featureId, i))
            self.index.append(IndexItem(eventItem.destination.featureId, i))

        # Ordenando o índice principal.
        self.index.sort(key=functools.cmp_to_key(self.compareIndexItems))

        # Montando o índice primário.
        self.primaryIndex.clear()
        featureId = -1
        indexItem = None
        for i, indexItem in enumerate(self.index):
            if indexItem.featureId != featureId:
                featureId = indexItem.featureId
                self.primaryIndex.append(IndexItem(featureId, i))

    def reportUnexpectedRelations(self, log: Message) -> None:
        log.append(
            "Erro! Impossível continuar! "
            "Encontradas relações topológicas inesperadas.\n"
            "São esperadas somente relações de encosta, "
            "entretanto foram encontradas as relações:"
        )

        if self.err:
            for item in self.err:
                log.append(
                    f"    - FID {str(item.source.featureId + 1)}"
                    + (
                        " toca em FID "
                        if item.relationType == 1
                        else " intercepta FID "
                    )
                    + f"{item.destination.featureId + 1}"
                )
            log.append(f"    Total de relações: {str(len(self.err))}.\n")
            log.append(
                "Consulte a documentação deste aplicativo para mais "
                "detalhes sobre as relações topológicas esperadas e inesperadas.\n"
                "Confira a topologia e execute o processamento novamente."
            )
