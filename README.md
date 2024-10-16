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

2 - Abre os arquivos SHP e em cada um:  (SHPFeatureSetDAO.load_feature_set)
  2.1 - Cria uma instância de FeatureSet
  2.2 - Cria uma variável new_feature_id que recebe como valor o tamanho da lista de feições do arquivo

  2.3 - Para cada feição:
    2.3.1 - Obtém a geometria da feição
    2.3.2 - Identifica se é uma geometria multi-part
    2.3.3 - Se não for, e a quantidade de vértices na geometria encontrada for igual à 1, adiciona uma observação da Feature criada (2.3.4.1)

    2.3.4 - Para cada parte encontrada:
      2.3.4.1 - Cria uma instância de Feature
      2.3.4.2 - Se iterando pela segunda parte em diante, seta o ID da Feature com new_feature_id e a incrementa

      2.3.4.3 - Para cada ponto ou vértice na parte:
        2.3.4.3.1 - Cria uma instância de Vertex com as coordenadas e o boolean last quando chega no último vértice

      2.3.4.4 - Para cada Vertex criado (2.3.3.3.1):
        2.3.4.4.1 - Obtém o Vertex seguinte e cria um Segment composto pelos dois

      2.3.4.5 - Salva ambas as listas na instância de Feature (2.3.3.1)

      2.3.4.6 - Se iterando na primeira parte:
        2.3.4.6.1 - Adiciona a Feature (2.3.3.1) no FeatureSet (2.1) dentro de featuresList
      2.3.4.7 - Se não:
        2.3.4.7.1 - Adiciona a Feature (2.3.3.1) no FeatureSet (2.1) dentro de newFeaturesList

3 - Inicia a classificação (Controller.classifyWaterBasin)
  3.1 - Se houve qualquer problema no carregamento da drenagem ou do limite da bacia, retorna o respectivo erro

  3.2 - Se não, cria uma instância de Classificator
  3.3 - Cria uma instância de Scanner e:  (Classificator.classifyWaterBasin)

    3.3.1 - Para cada uma das 3 listas de feições dos arquivos carregados (ignorando newFeaturesList do limite da bacia):
      3.3.1.1 - Para cada feição:
        3.3.1.1.1 - Se foi encontrado mais de um vértice na geometria:

          3.3.1.1.1.1 - Para cada segmento:
            3.3.1.1.1.1.1 - Adiciona uma instância de ScanLine com eventType = 0, vertex = segmento.a e o segmento em si como segmentA em Scanner.list
            3.3.1.1.1.1.2 - Adiciona uma instância de ScanLine com eventType = 1, vertex = segmento.b e o segmento em si como segmentA em Scanner.list

    # TODO: PROBLEM IS PROBABLY IN THIS CONVERSION:
    3.3.2 - Ordena as instâncias de ScanLine criadas (3.3.1.1.1.1.1 e 3.3.1.1.1.1.2) a partir de:
      3.3.2.1 - A coordenada x de scanLine.vertex
      3.3.2.2 - scanLine.eventType = 0 + a coordenada y de scanLine.vertex
      3.3.2.3 - scanLine.eventType = 1 + a menor coordenada x dentre os vértices de scanline.segmentA
      3.3.2.4 - a.eventType == 1 + b.eventType == 0 ou
      3.3.2.5 - a.eventType == 2 + b.eventType == 1 ou
      3.3.2.6 - a.eventType == 0 + b.eventType == 2

    3.3.3 - Iniciando a partir da última scanLine em scanner.list, para cada scanLine:  (Scanner.scanPlane)
      3.3.3.1 - Se a coordenada x de scanLine.vertex for menor que a última processada:
        3.3.3.1.1 - (Scanner.processScanPoints)
```

TODO:
- A few of our model and utility classes are already covered by PyQT5/PyQT6 and could be replaced
- Python camel_case naming convention should be followed for vars/attrs/funcs (pylintrc: C0103)
