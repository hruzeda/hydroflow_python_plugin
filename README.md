Plugin to compute drainage orders in drainage basins using Strahler and Shreve methods, and to optimize monitoring stations distribution using the Sharp method.

Created with Plugin Builder.

This a fork/rewrite of https://github.com/sistemalabgis/hydroflow that also integrates https://github.com/leonardguedes/MonitorPoint/blob/main/MonitorPointcode.

```
1 - Janela da Plugin abre com campos para:
  - SHP da drenagem
  - SHP do limite da bacia
  - Tolerância (em pixels) para os cálculos
  - Shreve
  - Strahler
  - Sugestão de pontos para monitoramento


# SHPFeatureSetDAO.load_feature_set
2 - Abre os arquivos SHP e em cada um:
  - Cria uma instância de FeatureSet

  - Para cada feição:
    - Obtém a geometria da feição
    - Identifica se é uma geometria multi-part
    - Se não for, e a quantidade de vértices na geometria encontrada for igual à 1
        adiciona uma observação na Feature criada

    - Para cada parte encontrada:
      - Cria uma instância de Feature
      - A partir da primeira parte, cria novas feições para cada outra parte

      - Para cada ponto ou vértice na parte:
        - Cria uma instância de Vertex com as coordenadas e o boolean last para a ultima parte

      - Para cada Vertex criado:
        - Obtém o Vertex seguinte e cria um Segment composto pelos dois

      - Salva ambas as listas na instância de Feature

    - Insere a Feature no FeatureSet


# Controller.classifyWaterBasin
3 - Se houve qualquer problema no carregamento da drenagem ou do limite da bacia, retorna o
      respectivo erro
  - Se não, cria uma instância de Classificator outra de Scanner

  # Classificator.classifyWaterBasin
  - Para cada uma das 3 listas de Features dos arquivos carregados
      (hidro.features, hidro.newFeatures, limite.features):

    - Para cada Feature:
      - Para cada segmento:
        - Adiciona uma instância de ScanLine com
            eventType = 0,
            vertex = segmento.a,
            segmentA = segmento
          em Scanner.list

        - Adiciona uma instância de ScanLine com
            eventType = 1,
            vertex = segmento.b,
            segmentA = segmento
          em Scanner.list

    - Ordena as instâncias de ScanLine criadas a partir de:
      - A coordenada x de scanLine.vertex
      - scanLine.eventType = 0 + a coordenada y de scanLine.vertex
      - scanLine.eventType = 1 + a menor coordenada x dentre os vértices de scanline.segmentA
      - a.eventType == 1 + b.eventType == 0 ou
        a.eventType == 2 + b.eventType == 1 ou
        a.eventType == 0 + b.eventType == 2

    # Classificator.scanPlane
    - Iniciando a partir da última scanLine em scanner.list, para cada scanLine:

      - Se a coordenada x de scanLine.vertex for menor que a última processada:
        - Cria uma variável test  que receberá uma lista de booleanos

        # Classificator.processScanPoints
        - Para cada ScanVertex com mais de um segmento em Scanner.vertices
            cuja coordenada X esteja dentro da tolerância definida:

          - Para cada segmento:
            - Adiciona no array test o resultado do teste:
                scanVertex.vertex == segment.a and
                (segment.a.isExtremity() or segment.setId == 1)
                or
                scanVertex.vertex == segment.b and
                (segment.b.isExtremity() or segment.setId == 1)

          - Novamente para cada segmento, e o segmento a seguir:
            - Se test for verdadeiro em ambas as posições:
              - Adiciona uma instância de Relation de tipo 0 (encosta) em
                  Classificator.topologicalRelations com ambos os segmentos

            - Se test for verdadeiro em uma das posições apenas:
              - Adiciona uma instância de Relation de tipo 1 (toca) em
                  Classificator.topologicalRelations com ambos os segmentos

            - Se test for verdadeiro em uma das posições apenas:
              - Adiciona uma instância de Relation de tipo 2 (intercepta) em
                  Classificator.topologicalRelations com ambos os segmentos

      - Cria uma instância de ScanVertex com os valores da scanLine atual,
          ou adiciona seus segmentos no ScanVertex existente de mesmo vértice (se houver)

      - Se scanLine.eventType == 0:
        - Insere o segmento a da scanLine na lista da instância de Position
            em Classificator.position

        - Se há um segmento na posição imediatamente anterior, ou imediatamente seguinte
            ao recém inserido na lista de Classificator.position:
          - Se o dado segmento e o inserido se interseccionam e a intersecção ocorre
              em uma das extremidade de ambos:
            - Adiciona um novo ScanLine na lista de Scanner com ambos os segmentos
                e eventType = 2 (intersecção)

      - Se scanLine.eventType == 1:
        - Procura o membro de Classificator.position para o segmento A de scanLine
        - Se há um segmento na posição imediatamente anterior e um na imediatamente seguinte
            ao recuperado na lista de Classificator.position:
          - Se o dado segmento e o seguinte se interseccionam e a intersecção ocorre
              em uma das extremidade de ambos:
            - Adiciona um novo ScanLine na lista de Scanner com ambos os segmentos
                e eventType = 2 (intersecção)
        - Exclui o membro encontrado de Classificator.position

      - Se scanLine.eventType == 2:
        - Se scanVertex.vertex não for nenhuma das extremidades dos segmentos A ou B:
          - Procura o membro de Classificator.position para o segmento A de scanLine
          - Procura o membro de Classificator.position para o segmento B de scanLine
          - Inverte a posição dos dois membros em Classificator.position
          - Se há um segmento na posição imediatamente anterior do membro para o segmento A,
              ou um imediatamente seguinte ao membro para o segmento B:
            - Se o dado segmento e o seguinte se interseccionam e a intersecção ocorre
                em uma das extremidade de ambos:
              - Adiciona um novo ScanLine na lista de Scanner com ambos os segmentos
                  e eventType = 2 (intersecção)

    # Classificator.buildTree
    - Se não foi encontrada a foz, retorna o respectivo erro
    - Caso contrário,


```

TODO:
- A few of our model and utility classes are already covered by PyQT5/PyQT6 and could be replaced
- Python camel_case naming convention should be followed for vars/attrs/funcs (pylintrc: C0103)
