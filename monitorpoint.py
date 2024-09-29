import json

from qgis.core import Qgis, QgsMessageLog, QgsVectorLayer

# CRIA DICIONÁRIO COM ID E ORDEM DE CADA CURSO DA HIDROGRAFIA, COM BASE NOS ARQUIVOS GERADOS PELO HIDROFLOW

vlayer = QgsVectorLayer(
    "hidro_paraibunac_processado.shp",
    "Ports layer",
    "ogr",
)
fid_shreve_map = [None] * vlayer.featureCount()
features = vlayer.getFeatures()
for feature in features:
    fid1 = int(feature.id())
    fid2 = int(feature["Shreve"])
    fid_shreve_map[fid1] = fid2

QgsMessageLog.logMessage(
    f"Shreve das feições:\n{fid_shreve_map}", "HydroFlow", Qgis.Info
)

# REALIZA O CALCULO SHARP - Gera uma lista de resultados para SHARP

desired_n_segments = 6
Ma = max(fid_shreve_map)
QgsMessageLog.logMessage(f"Ordem da foz: {Ma}", "HydroFlow", Qgis.Info)
l_sharp = set()

while len(l_sharp) != desired_n_segments:
    T = (Ma + 1) / 2
    l_sharp.add(T)
    Ma = T

l_sharp = list(l_sharp)
l_sharp.sort(reverse=True)
QgsMessageLog.logMessage(f"Resultados de SHARP:\n{l_sharp}", "HydroFlow", Qgis.Info)

# BUSCA EM ÁRVORE DO ID ADEQUADO PARA CADA RESULTADO DE SHARP (RESULTADO PARCIAL)

final_result = {}
for i, sharp in enumerate(l_sharp):
    stringified = str(sharp)
    rounded = round(sharp)
    found = False
    for feature_id, shreve in enumerate(fid_shreve_map):
        if shreve == rounded:
            found = True
            if str(sharp) not in final_result:
                final_result[stringified] = [feature_id]
            else:
                final_result[stringified].append(feature_id)

    dif = 1
    while not found and dif < len(fid_shreve_map):
        for feature_id, shreve in enumerate(fid_shreve_map):
            if shreve == rounded - dif or shreve == rounded + dif:
                found = True
                if stringified not in final_result:
                    final_result[stringified] = [feature_id]
                else:
                    final_result[stringified].append(feature_id)
        dif += 1

or_str_dict = {}
for key in final_result.keys():
    or_str_dict[key] = " or ".join([f"id={result}" for result in final_result[key]])

QgsMessageLog.logMessage(
    f"Where:\n{json.dumps(or_str_dict)}",
    "HydroFlow",
    Qgis.Info,
)
QgsMessageLog.logMessage(
    f"Resultado final:\n{json.dumps(final_result)}", "HydroFlow", Qgis.Info
)
