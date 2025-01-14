#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# pylint: disable=invalid-name

"""
Biblioteca Gráfica / Graphics Library.

Desenvolvido por: Gustavo Braga
Disciplina: Computação Gráfica
Data: 13 de setembro de 2021
"""

import utils
import numpy as np
import time         # Para operações com tempo

import gpu          # Simula os recursos de uma GPU
import math

class GL:
    """Classe que representa a biblioteca gráfica (Graphics Library)."""

    width = 800   # largura da tela
    height = 600  # altura da tela
    near = 0.01   # plano de corte próximo
    far = 1000    # plano de corte distante
    sampling_X_ = 2
    
    eye = None
    mvp = None
    orientation = None
    view_to_point = None
    world_to_view = None
    point_to_screen = None
    transformation_matrix_stack = None
    model_to_world = []

    @staticmethod
    def setup(width, height, near=0.01, far=1000):
        """Define parametros para câmera de razão de aspecto, plano próximo e distante."""
        print("\n=== Rasterizer Setup ===")
        GL.width = width
        GL.height = height
        GL.near = near
        GL.far = far

        try:
            s = int(input("\nSampling nXn: (ex: 2 is 2x2, 3 is 3x3, ...)\nDefault is 2x2, press enter to use default.\n"))
            GL.sampling_X_ = s

        except: 
            print("Using default 2x2 sampling")

        print("Sampling: " + str(GL.sampling_X_) + "X" + str(GL.sampling_X_))

        utils.Rasterizer.setup(gpu.GPU, GL.width, GL.height, GL.sampling_X_, True)
        GL.point_to_screen = utils.point_screen(width, height)
        print("\n======================================================================")

    @staticmethod
    def viewpoint(position, orientation, fieldOfView):
        """Função usada para renderizar (na verdade coletar os dados) de Viewpoint."""
        # Na função de viewpoint você receberá a posição, orientação e campo de visão da
        # câmera virtual. Use esses dados para poder calcular e criar a matriz de projeção
        # perspectiva para poder aplicar nos pontos dos objetos geométricos.

        print("\n=== Viewpoint ===")
        GL.view_to_point = utils.view_point(fieldOfView, GL.near, GL.far, GL.width, GL.height)
        GL.world_to_view = utils.world_view_lookat_simple(position, orientation)

    @staticmethod
    def transform_in(translation, scale, rotation):
        """Função usada para renderizar (na verdade coletar os dados) de Transform."""
        # A função transform_in será chamada quando se entrar em um nó X3D do tipo Transform
        # do grafo de cena. Os valores passados são a escala em um vetor [x, y, z]
        # indicando a escala em cada direção, a translação [x, y, z] nas respectivas
        # coordenadas e finalmente a rotação por [x, y, z, t] sendo definida pela rotação
        # do objeto ao redor do eixo x, y, z por t radianos, seguindo a regra da mão direita.
        # Quando se entrar em um nó transform se deverá salvar a matriz de transformação dos
        # modelos do mundo em alguma estrutura de pilha.

        print("\n=== Transform in ===")
        GL.transformation_matrix_stack = utils.model_world(translation, rotation, scale)
        if len(GL.model_to_world) > 0: GL.transformation_matrix_stack = np.dot(GL.model_to_world[len(GL.model_to_world) - 1], GL.transformation_matrix_stack)

        GL.model_to_world += [GL.transformation_matrix_stack]
        GL.mvp = utils.mvp(GL)

    @staticmethod
    def transform_out():
        """Função usada para renderizar (na verdade coletar os dados) de Transform."""
        # A função transform_out será chamada quando se sair em um nó X3D do tipo Transform do
        # grafo de cena. Não são passados valores, porém quando se sai de um nó transform se
        # deverá recuperar a matriz de transformação dos modelos do mundo da estrutura de
        # pilha implementada.

        print("=== Transform out ===")
        if len(GL.model_to_world) > 0: GL.model_to_world.pop()
    
    @staticmethod
    def triangleSet(point, colors):
        """Função usada para renderizar TriangleSet."""
        # Nessa função você receberá pontos no parâmetro point, esses pontos são uma lista
        # de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x do
        # primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da
        # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e
        # assim por diante.
        # No TriangleSet os triângulos são informados individualmente, assim os três
        # primeiros pontos definem um triângulo, os três próximos pontos definem um novo
        # triângulo, e assim por diante.
        # O parâmetro colors é um dicionário com os tipos cores possíveis, para o TriangleSet
        # você pode assumir o desenho das linhas com a cor emissiva (emissiveColor).
        # print("TriangleSet")
        
        ## Transformations
        screen_points = utils.transform_points(point, GL)
        
        ## Raster
        triangles = []
        input_color = colors if utils.Light.has_light else colors["diffuseColor"]

        for p in range(0, len(screen_points) - 2, 3):
            triangles += [[screen_points[p], screen_points[p + 1], screen_points[p + 2]]]
        
        utils.Rasterizer.render(triangles=triangles, colors=input_color)

    @staticmethod
    def triangleStripSet(point, stripCount, colors):
        """Função usada para renderizar TriangleStripSet."""
        # A função triangleStripSet é usada para desenhar tiras de triângulos interconectados,
        # você receberá as coordenadas dos pontos no parâmetro point, esses pontos são uma
        # lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x
        # do primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da
        # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e assim
        # por diante. No TriangleStripSet a quantidade de vértices a serem usados é informado
        # em uma lista chamada stripCount (perceba que é uma lista). Ligue os vértices na ordem,
        # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
        # depois 2, 3 e 4, e assim por diante. Cuidado com a orientação dos vértices, ou seja,
        # todos no sentido horário ou todos no sentido anti-horário, conforme especificado.
        # print("TriangleStripSet")

        ## Transformations
        screen_points = utils.transform_points(point, GL)
        
        ## Raster
        triangles = []
        input_color = colors if utils.Light.has_light else colors["diffuseColor"]

        for i in range(stripCount[0] - 2):
            triangles += [[screen_points[i + 2], screen_points[i + 1], screen_points[i]]]
            if i % 2 == 0: triangles += [[screen_points[i], screen_points[i + 1], screen_points[i + 2]]]
        
        utils.Rasterizer.render(triangles=triangles, colors=input_color)

    @staticmethod
    def indexedTriangleStripSet(point, index, colors):
        """Função usada para renderizar IndexedTriangleStripSet."""
        # A função indexedTriangleStripSet é usada para desenhar tiras de triângulos
        # interconectados, você receberá as coordenadas dos pontos no parâmetro point, esses
        # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor
        # da coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto, point[2]
        # o valor z da coordenada z do primeiro ponto. Já point[3] é a coordenada x do
        # segundo ponto e assim por diante. No IndexedTriangleStripSet uma lista informando
        # como conectar os vértices é informada em index, o valor -1 indica que a lista
        # acabou. A ordem de conexão será de 3 em 3 pulando um índice. Por exemplo: o
        # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
        # depois 2, 3 e 4, e assim por diante. Cuidado com a orientação dos vértices, ou seja,
        # todos no sentido horário ou todos no sentido anti-horário, conforme especificado.
        # print("IndexedTriangleStripSet")

        ## Transformations
        screen_points = utils.transform_points(point, GL)
        
        ## Raster
        triangles = []
        input_color = colors if utils.Light.has_light else colors["diffuseColor"]

        for i in range(len(index) - 3):
            triangles += [[screen_points[index[i + 2]], screen_points[index[i + 1]], screen_points[index[i]]]]
            if i % 2 == 0: triangles += [[screen_points[index[i]], screen_points[index[i + 1]], screen_points[index[i + 2]]]]
        
        utils.Rasterizer.render(triangles=triangles, colors=input_color)

    @staticmethod
    def box(size, colors):
        """Função usada para renderizar Boxes."""
        # A função box é usada para desenhar paralelepípedos na cena. O Box é centrada no
        # (0, 0, 0) no sistema de coordenadas local e alinhado com os eixos de coordenadas
        # locais. O argumento size especifica as extensões da caixa ao longo dos eixos X, Y
        # e Z, respectivamente, e cada valor do tamanho deve ser maior que zero. Para desenha
        # essa caixa você vai provavelmente querer tesselar ela em triângulos, para isso
        # encontre os vértices e defina os triângulos.

        # print("Box")

        x = size[0]
        y = size[1]
        z = size[2]
        
        ## !! Cube Order, counter clock-wise
        # front, left, back, right, up, down
        square_p1 = (-x, -y, z)
        square_p2 = (x, -y, z)
        square_p3 = (x, y, z)
        square_p4 = (-x, y, z)
        square_p5 = (-x, y, -z)
        square_p6 = (x, y, -z)
        square_p7 = (-x, -y, -z)
        square_p8 = (x, -y, -z)

        point = [
            square_p1, square_p2, square_p3,
            square_p3, square_p4, square_p1,

            square_p7, square_p1, square_p4,
            square_p4, square_p5, square_p7,
            
            square_p8, square_p7, square_p5,
            square_p5, square_p6, square_p8,
            
            square_p8, square_p6, square_p2,
            square_p2, square_p6, square_p3,
            
            square_p6, square_p5, square_p4,
            square_p4, square_p3, square_p6,
            
            square_p8, square_p7, square_p1,
            square_p1, square_p2, square_p8
        ]

        point = list(sum(point, ()))
        
        ## Raster
        GL.triangleSet(point, colors)

    @staticmethod
    def indexedFaceSet(coord, coordIndex, colorPerVertex, color, colorIndex,
                       texCoord, texCoordIndex, colors, current_texture):
        """Função usada para renderizar IndexedFaceSet."""
        # A função indexedFaceSet é usada para desenhar malhas de triângulos. Ela funciona de
        # forma muito simular a IndexedTriangleStripSet porém com mais recursos.
        # Você receberá as coordenadas dos pontos no parâmetro cord, esses
        # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim coord[0] é o valor
        # da coordenada x do primeiro ponto, coord[1] o valor y do primeiro ponto, coord[2]
        # o valor z da coordenada z do primeiro ponto. Já coord[3] é a coordenada x do
        # segundo ponto e assim por diante. No IndexedFaceSet uma lista de vértices é informada
        # em coordIndex, o valor -1 indica que a lista acabou.
        # A ordem de conexão será de 3 em 3 pulando um índice. Por exemplo: o
        # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
        # depois 2, 3 e 4, e assim por diante.
        # Adicionalmente essa implementação do IndexedFace aceita cores por vértices, assim
        # se a flag colorPerVertex estiver habilitada, os vértices também possuirão cores
        # que servem para definir a cor interna dos poligonos, para isso faça um cálculo
        # baricêntrico de que cor deverá ter aquela posição. Da mesma forma se pode definir uma
        # textura para o poligono, para isso, use as coordenadas de textura e depois aplique a
        # cor da textura conforme a posição do mapeamento. Dentro da classe GPU já está
        # implementadado um método para a leitura de imagens.
        # print("IndexedFaceSet : ")

        ## Transformations
        screen_points = utils.transform_points(coord, GL)
        
        ## Raster
        vertex_color = colorPerVertex and color and colorIndex
        has_texture = texCoord and texCoordIndex and current_texture

        if vertex_color: input_color = []
        elif utils.Light.has_light: input_color = colors
        else: input_color = colors["diffuseColor"]

        triangles = []
        uvs = []

        for i in range(0, len(coordIndex) - 3, 4):
            triangles += [[screen_points[coordIndex[i]], screen_points[coordIndex[i + 1]], screen_points[coordIndex[i + 2]]]]

            if has_texture:
                offset_1 = (texCoordIndex[i]) * 2
                offset_2 = (texCoordIndex[i + 1]) * 2
                offset_3 = (texCoordIndex[i + 2]) * 2

                uvs += [[
                    [texCoord[offset_1], texCoord[offset_1 + 1]],
                    [texCoord[offset_2], texCoord[offset_2 + 1]],
                    [texCoord[offset_3], texCoord[offset_3 + 1]]
                ]]

            elif vertex_color:
                offset_1 = (colorIndex[i]) * 3
                offset_2 = (colorIndex[i + 1]) * 3
                offset_3 = (colorIndex[i + 2]) * 3

                input_color += [[
                    [color[offset_1], color[offset_1 + 1], color[offset_1 + 2]], 
                    [color[offset_2], color[offset_2 + 1], color[offset_2 + 2]], 
                    [color[offset_3], color[offset_3 + 1], color[offset_3 + 2]]
                ]]

        utils.Rasterizer.render(triangles=triangles, colors=input_color, vertex_color=vertex_color, texture=current_texture, uv=uvs, has_texture=has_texture)
        
    @staticmethod
    def sphere(radius, colors):
        """Função usada para renderizar Esferas."""
        # A função sphere é usada para desenhar esferas na cena. O esfera é centrada no
        # (0, 0, 0) no sistema de coordenadas local. O argumento radius especifica o
        # raio da esfera que está sendo criada. Para desenha essa esfera você vai
        # precisar tesselar ela em triângulos, para isso encontre os vértices e defina
        # os triângulos.

        print("Sphere : radius = {0}".format(radius)) # imprime no terminal o raio da esfera
        print("Sphere : colors = {0}".format(colors)) # imprime no terminal as cores

        sector_count = 12
        stack_count = 12
        point = []

        sector_step = 2 * math.pi / sector_count;
        stack_step = math.pi / stack_count;

        for i in range(stack_count):
            stack_angle = math.pi / 2 - i * stack_step;
            xy = radius * math.cos(stack_angle);
            z = radius * math.sin(stack_angle);

            for j in range(sector_count):
                sector_angle = j * sector_step

                x = xy * math.cos(sector_angle);
                y = xy * math.sin(sector_angle);
                point += [x, y, z];
        
        ## Transformations
        screen_points = utils.transform_points(point, GL)
        indices = []
        triangles = []

        # for i in range(stack_count):
        #     k1 = i * (sector_count + 1);
        #     k2 = k1 + sector_count + 1;

        #     for j in range(sector_count):
        #         if i != 0:
        #             indices += [k1, k1 + 1, k2]

        #         if i != (stack_count - 1):
        #             indices += [k1 + 1, k2 + 1, k2]
                
        #         k1 += 1
        #         k2 += 1

        # for i in screen_points:
        #     print([int(i[0][0, 0]), int(i[1][0, 0])])
        #     gpu.GPU.draw_pixels([int(i[0][0, 0]), int(i[1][0, 0])], gpu.GPU.RGB8, [255, 255, 255])

        # return

        for i in range(stack_count):
            k1 = i * (sector_count + 1)
            k2 = k1 + sector_count + 1

            for j in range(sector_count):
                if (k1 + 1 >= len(screen_points) or k2 + 1 >= len(screen_points)): break
                if i != 0:
                    triangles += [[screen_points[k1], screen_points[k1 + 1], screen_points[k2]]]

                if i != (stack_count - 1):
                    triangles += [[screen_points[k1 + 1], screen_points[k2 + 1], screen_points[k2]]]
                
                k1 += 1
                k2 += 1

        # print(indices, len(screen_points))
        utils.Rasterizer.render(triangles=triangles, colors=colors)

    @staticmethod
    def navigationInfo(headlight):
        """Características físicas do avatar do visualizador e do modelo de visualização."""
        # O campo do headlight especifica se um navegador deve acender um luz direcional que
        # sempre aponta na direção que o usuário está olhando. Definir este campo como TRUE
        # faz com que o visualizador forneça sempre uma luz do ponto de vista do usuário.
        # A luz headlight deve ser direcional, ter intensidade = 1, cor = (1 1 1),
        # ambientIntensity = 0,0 e direção = (0 0 −1).

        # print("NavigationInfo : headlight = {0}".format(headlight)) # imprime no terminal
        if headlight:
            utils.Light.setup(ambient_intensity=0, color=[1, 1, 1], intensity=1, direction=[0, 0, -1])

    @staticmethod
    def directionalLight(ambientIntensity, color, intensity, direction):
        """Luz direcional ou paralela."""
        # Define uma fonte de luz direcional que ilumina ao longo de raios paralelos
        # em um determinado vetor tridimensional. Possui os campos básicos ambientIntensity,
        # cor, intensidade. O campo de direção especifica o vetor de direção da iluminação
        # que emana da fonte de luz no sistema de coordenadas local. A luz é emitida ao
        # longo de raios paralelos de uma distância infinita.

        # print("DirectionalLight : ambientIntensity = {0}".format(ambientIntensity))
        # print("DirectionalLight : color = {0}".format(color)) # imprime no terminal
        # print("DirectionalLight : intensity = {0}".format(intensity)) # imprime no terminal
        # print("DirectionalLight : direction = {0}".format(direction)) # imprime no terminal

        utils.Light.setup(ambient_intensity=ambientIntensity, color=color, intensity=intensity, direction=direction)

    @staticmethod
    def timeSensor(cycleInterval, loop):
        """Gera eventos conforme o tempo passa."""
        # Os nós TimeSensor podem ser usados para muitas finalidades, incluindo:
        # Condução de simulações e animações contínuas; Controlar atividades periódicas;
        # iniciar eventos de ocorrência única, como um despertador;
        # Se, no final de um ciclo, o valor do loop for FALSE, a execução é encerrada.
        # Por outro lado, se o loop for TRUE no final de um ciclo, um nó dependente do
        # tempo continua a execução no próximo ciclo. O ciclo de um nó TimeSensor dura
        # cycleInterval segundos. O valor de cycleInterval deve ser maior que zero.

        # Deve retornar a fração de tempo passada em fraction_changed

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        # print("TimeSensor : cycleInterval = {0}".format(cycleInterval)) # imprime no terminal
        # print("TimeSensor : loop = {0}".format(loop))
    
        # Esse método já está implementado para os alunos como exemplo
        epoch = time.time()  # time in seconds since the epoch as a floating point number.
        fraction_changed = (epoch % cycleInterval) / cycleInterval

        return fraction_changed

    @staticmethod
    def splinePositionInterpolator(set_fraction, key, keyValue, closed):
        """Interpola não linearmente entre uma lista de vetores 3D."""
        # Interpola não linearmente entre uma lista de vetores 3D. O campo keyValue possui
        # uma lista com os valores a serem interpolados, key possui uma lista respectiva de chaves
        # dos valores em keyValue, a fração a ser interpolada vem de set_fraction que varia de
        # zeroa a um. O campo keyValue deve conter exatamente tantos vetores 3D quanto os
        # quadros-chave no key. O campo closed especifica se o interpolador deve tratar a malha
        # como fechada, com uma transições da última chave para a primeira chave. Se os keyValues
        # na primeira e na última chave não forem idênticos, o campo closed será ignorado.

        # print("SplinePositionInterpolator : set_fraction = {0}".format(set_fraction))
        # print("SplinePositionInterpolator : key = {0}".format(key)) # imprime no terminal
        # print("SplinePositionInterpolator : keyValue = {0}".format(keyValue))
        # print("SplinePositionInterpolator : closed = {0}".format(closed))

        return utils.hermite_interpolation(key=key, keyValue=keyValue, closed=closed, set_fraction=set_fraction)

    @staticmethod
    def orientationInterpolator(set_fraction, key, keyValue):
        """Interpola entre uma lista de valores de rotação especificos."""
        # Interpola rotações são absolutas no espaço do objeto e, portanto, não são cumulativas.
        # Uma orientação representa a posição final de um objeto após a aplicação de uma rotação.
        # Um OrientationInterpolator interpola entre duas orientações calculando o caminho mais
        # curto na esfera unitária entre as duas orientações. A interpolação é linear em
        # comprimento de arco ao longo deste caminho. Os resultados são indefinidos se as duas
        # orientações forem diagonalmente opostas. O campo keyValue possui uma lista com os
        # valores a serem interpolados, key possui uma lista respectiva de chaves
        # dos valores em keyValue, a fração a ser interpolada vem de set_fraction que varia de
        # zeroa a um. O campo keyValue deve conter exatamente tantas rotações 3D quanto os
        # quadros-chave no key.

        # print("OrientationInterpolator : set_fraction = {0}".format(set_fraction))
        # print("OrientationInterpolator : key = {0}".format(key)) # imprime no terminal
        # print("OrientationInterpolator : keyValue = {0}".format(keyValue))

        return utils.linear_interpolation(key=key, keyValue=keyValue, set_fraction=set_fraction)

    # Para o futuro (Não para versão atual do projeto.)
    def vertex_shader(self, shader):
        """Para no futuro implementar um vertex shader."""

    def fragment_shader(self, shader):
        """Para no futuro implementar um fragment shader."""
    
    @staticmethod
    def pointLight(ambientIntensity, color, intensity, location):
        """Luz pontual."""
        # Fonte de luz pontual em um local 3D no sistema de coordenadas local. Uma fonte
        # de luz pontual emite luz igualmente em todas as direções; ou seja, é omnidirecional.
        # Possui os campos básicos ambientIntensity, cor, intensidade. Um nó PointLight ilumina
        # a geometria em um raio de sua localização. O campo do raio deve ser maior ou igual a
        # zero. A iluminação do nó PointLight diminui com a distância especificada.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("PointLight : ambientIntensity = {0}".format(ambientIntensity))
        print("PointLight : color = {0}".format(color)) # imprime no terminal
        print("PointLight : intensity = {0}".format(intensity)) # imprime no terminal
        print("PointLight : location = {0}".format(location)) # imprime no terminal

    @staticmethod
    def fog(visibilityRange, color):
        """Névoa."""
        # O nó Fog fornece uma maneira de simular efeitos atmosféricos combinando objetos
        # com a cor especificada pelo campo de cores com base nas distâncias dos
        # vários objetos ao visualizador. A visibilidadeRange especifica a distância no
        # sistema de coordenadas local na qual os objetos são totalmente obscurecidos
        # pela névoa. Os objetos localizados fora de visibilityRange do visualizador são
        # desenhados com uma cor de cor constante. Objetos muito próximos do visualizador
        # são muito pouco misturados com a cor do nevoeiro.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("Fog : color = {0}".format(color)) # imprime no terminal
        print("Fog : visibilityRange = {0}".format(visibilityRange))
