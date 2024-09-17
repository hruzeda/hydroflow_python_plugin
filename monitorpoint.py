from qgis.core import Qgis, QgsMessageLog, QgsVectorLayer

# CRIA DICIONÁRIO COM ID E ORDEM DE CADA CURSO DA HIDROGRAFIA, COM BASE NOS ARQUIVOS GERADOS PELO HIDROFLOW

vlayer = QgsVectorLayer(
    "D:\\heinr\\Downloads\\Hidro_class.shp",
    "Ports layer",
    "ogr",
)
orderDict = {}
features = vlayer.getFeatures()
for feature in features:
    chave = int(feature.id())
    valor = int(feature["Shreve"])
    orderDict[chave] = valor

QgsMessageLog.logMessage(
    f"Dicionário ID-Ordem:\n{orderDict}", "HydroFlow", Qgis.Info
)

# CRIA TOPOLOGIA PARA BUSCA, COM BASE NO ARQUIVO GERADO NO HIDROFLOW

topology_file = open(
    "D:\\heinr\\Downloads\\Hidro_class_topo.txt",
    "r",
    encoding="UTF-8",
)
topology_file.readline()
topology = {}
line = topology_file.readline()
mouth = None
for line in topology_file:
    par = line[:-1].split(";")
    chave = int(par[0])
    valor = int(par[-1])
    if mouth is None:
        mouth = chave
    if chave not in topology:
        topology[chave] = []
    topology[chave].append(valor)

QgsMessageLog.logMessage(f"Topologia:\n{topology}", "HydroFlow", Qgis.Info)

# REALIZA O CALCULO SHARP - Gera uma lista de resultados para SHARP

desired_n_segments = 10
Ma = orderDict[mouth]
l_sharp = []

while len(l_sharp) != desired_n_segments:
    T = (Ma + 1) / 2
    l_sharp.append(T)

    if len(l_sharp) == desired_n_segments:
        break

    T2 = (T + 1) / 2
    l_sharp.append(T2)

    if len(l_sharp) == desired_n_segments:
        break

    T3 = T + T2
    l_sharp.append(T3)
    Ma = T2

l_sharp.sort(reverse=True)

# BUSCA EM ÁRVORE DO ID ADEQUADO PARA CADA RESULTADO DE SHARP (RESULTADO PARCIAL)

l_smaller_node_id = [mouth] * len(l_sharp)


def search(node_id, l_sharp, l_smaller_node_id, current_sharp, orderDict, topology):
    dif = abs(orderDict[node_id] - l_sharp[current_sharp])
    smaller_dif = abs(
        orderDict[l_smaller_node_id[current_sharp]] - l_sharp[current_sharp]
    )

    if dif < smaller_dif:
        l_smaller_node_id[current_sharp] = node_id

    if orderDict[node_id] <= l_sharp[current_sharp]:
        current_sharp += 1
        if current_sharp == len(l_sharp):
            return
        search(
            node_id, l_sharp, l_smaller_node_id, current_sharp, orderDict, topology
        )

    elif orderDict[node_id] >= l_sharp[current_sharp]:
        for child_node_id in topology[node_id]:
            search(
                child_node_id,
                l_sharp,
                l_smaller_node_id,
                current_sharp,
                orderDict,
                topology,
            )
            if abs(
                orderDict[l_smaller_node_id[current_sharp]] - l_sharp[current_sharp]
            ) < abs(
                orderDict[l_smaller_node_id[current_sharp]] - l_sharp[current_sharp]
            ):
                l_smaller_node_id[current_sharp] = l_smaller_node_id[current_sharp]


search(mouth, l_sharp, l_smaller_node_id, 0, orderDict, topology)
QgsMessageLog.logMessage(
    f"Resultado parcial:\n{str(l_smaller_node_id)}", "HydroFlow", Qgis.Info
)

# BUSCA DE IDS IGUAIS AOS ENCONTRADOS NA PRIMEIRA BUSCA (RESULTADO FINAL)

magnitudes = []
final_result = {}
for node_id in l_smaller_node_id:
    magnitudes.append(orderDict[node_id])
    final_result[orderDict[node_id]] = []


def find_equal_ids(
    node_id, magnitudes, current_pos, orderDict, topology, final_result
):
    if current_pos == len(magnitudes):
        return
    if orderDict[node_id] == magnitudes[current_pos]:
        final_result[magnitudes[current_pos]].append(node_id)
    if orderDict[node_id] <= magnitudes[current_pos]:
        find_equal_ids(
            node_id, magnitudes, current_pos + 1, orderDict, topology, final_result
        )
    else:
        for child_node_id in topology[node_id]:
            find_equal_ids(
                child_node_id,
                magnitudes,
                current_pos,
                orderDict,
                topology,
                final_result,
            )


find_equal_ids(mouth, magnitudes, 0, orderDict, topology, final_result)
l_result_final = []
where = ""

for id in final_result:
    for i in final_result[id]:
        l_result_final.append(i)
        where += " or id=" + str(i)
QgsMessageLog.logMessage(f"Where:\n{where[4:]}", "HydroFlow", Qgis.Info)

QgsMessageLog.logMessage(
    f"Resultado final:\n{l_result_final}", "HydroFlow", Qgis.Info
)
