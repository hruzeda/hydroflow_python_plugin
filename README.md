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
  2.1 - Cria uma instância de FeatureSet

  2.2 - Para cada feição:
    2.2.1 - Obtém a geometria da feição
    2.2.2 - Identifica se é uma geometria multi-part
    2.2.3 - Se não for, e a quantidade de vértices na geometria encontrada for igual à 1
            adiciona uma observação na Feature criada (2.3.4.1)

    2.2.4 - Para cada parte encontrada:
      2.2.4.1 - Cria uma instância de Feature
      2.2.4.2 - A partir da primeira parte, cria novas feições para cada outra parte

      2.2.4.3 - Para cada ponto ou vértice na parte:
        2.2.4.3.1 - Cria uma instância de Vertex com as coordenadas e o boolean last para a ultima parte

      2.2.4.4 - Para cada Vertex criado (2.3.3.3.1):
        2.2.4.4.1 - Obtém o Vertex seguinte e cria um Segment composto pelos dois

      2.2.4.5 - Salva ambas as listas na instância de Feature (2.3.3.1)

# Controller.classifyWaterBasin
3 - Inicia a classificação
  3.1 - Se houve qualquer problema no carregamento da drenagem ou do limite da bacia, retorna o
        respectivo erro

  3.2 - Se não, cria uma instância de Classificator outra de Scanner

  # Classificator.classifyWaterBasin
  3.3 - Para cada uma das 3 listas de Features dos arquivos carregados
          (hidro.features, hidro.newFeatures, limite.features):

    3.3.1 - Para cada Feature:
      3.3.1.1 - Para cada segmento:
        3.3.1.1.1 - Adiciona uma instância de ScanLine com
                      eventType = 0,
                      vertex = segmento.a,
                      o segmento em si como segmentA
                    em Scanner.list

        3.3.1.1.2 - Adiciona uma instância de ScanLine com
                      eventType = 1,
                      vertex = segmento.b,
                      o segmento em si como segmentA
                    em Scanner.list

    3.3.2 - Ordena as instâncias de ScanLine criadas (3.3.1.1.1 e 3.3.1.1.2) a partir de:
      3.3.2.1 - A coordenada x de scanLine.vertex
      3.3.2.2 - scanLine.eventType = 0 + a coordenada y de scanLine.vertex
      3.3.2.3 - scanLine.eventType = 1 + a menor coordenada x dentre os vértices de scanline.segmentA
      3.3.2.4 - a.eventType == 1 + b.eventType == 0 ou
      3.3.2.5 - a.eventType == 2 + b.eventType == 1 ou
      3.3.2.6 - a.eventType == 0 + b.eventType == 2

    # Classificator.scanPlane
    3.3.3 - Iniciando a partir da última scanLine em scanner.list, para cada scanLine:

      3.3.3.1 - Se a coordenada x de scanLine.vertex for menor que a última processada:
        3.3.3.1.1 - Cria uma variável test  que receberá uma lista de booleanos

        # Classificator.processScanPoints
        3.3.3.1.2 - Para cada ScanVertex com mais de um segmento em Scanner.vertices
                    cuja coordenada X esteja dentro da tolerância definida:

          3.3.3.1.2.1 - Para cada segmento:
            3.3.3.1.2.1.1 - Adiciona no array test o resultado do teste:
                            scanVertex.vertex == segment.a and
                            (segment.a.isExtremity() or segment.setId == 1)
                            or
                            scanVertex.vertex == segment.b and
                            (segment.b.isExtremity() or segment.setId == 1)

          3.3.3.1.2.2 - Novamente para cada segmento, e o segmento a seguir:
            3.3.3.1.2.2.1 - Se test for verdadeiro em ambas as posições:
              3.3.3.1.2.2.1.1 - Adiciona uma instância de Relation de tipo 0 (encosta) em
                                Classificator.topologicalRelations com ambos os segmentos

            3.3.3.1.2.2.2 - Se test for verdadeiro em uma das posições apenas:
              3.3.3.1.2.2.2.1 - Adiciona uma instância de Relation de tipo 1 (toca) em
                                Classificator.topologicalRelations com ambos os segmentos

            3.3.3.1.2.2.3 - Se test for verdadeiro em uma das posições apenas:
              3.3.3.1.2.2.3.1 - Adiciona uma instância de Relation de tipo 2 (intercepta) em
                                Classificator.topologicalRelations com ambos os segmentos

      3.3.3.2 - Cria uma instância de ScanVertex com os valores da scanLine atual,
                ou adiciona seus segmentos no ScanVertex existente de mesmo vértice (se houver)

      3.3.3.3 - Se scanLine.eventType == 0:
        3.3.3.3.1 - Insere o segmento a da scanLine na lista da instância de Position
                    em Classificator.position

        3.3.3.3.2 - Se há um segmento na posição imediatamente anterior, ou imediatamente seguinte
                    ao recém inserido (3.3.3.3.1) na lista de Classificator.position:
          3.3.3.3.2.1 - Se o dado segmento e o inserido se interseccionam e a intersecção ocorre
                        em uma das extremidade de ambos:
            3.3.3.3.2.1.1 - Adiciona um novo ScanLine na lista de Scanner com ambos os segmentos
                            e eventType = 2 (intersecção)

      3.3.3.4 - Se scanLine.eventType == 1:
        3.3.3.4.1 - Procura o membro de Classificator.position para o segmento de scanLine
        3.3.3.4.2 - Se há um segmento na posição imediatamente anterior e um na imediatamente seguinte
                    ao recuperado (3.3.3.4.1) na lista de Classificator.position:
          3.3.3.4.2.1 - Se o dado anterior e o seguinte se interseccionam e a intersecção ocorre
                        em uma das extremidade de ambos:
            3.3.3.4.2.1.1 - Adiciona um novo ScanLine na lista de Scanner com ambos os segmentos
                            e eventType = 2 (intersecção)
        3.3.3.4.3 - Exclui o membro encontrado de Classificator.position

      3.3.3.5 - Se scanLine.eventType == 2:

```

TODO:
- A few of our model and utility classes are already covered by PyQT5/PyQT6 and could be replaced
- Python camel_case naming convention should be followed for vars/attrs/funcs (pylintrc: C0103)
