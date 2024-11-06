import pyautogui
import time
import cv2
import numpy as np
import random
import keyboard

possible_movements = [ (-1, -1), (-1,  0), (-1,  1),
                           ( 0, -1),          ( 0,  1),
                           ( 1, -1), ( 1,  0), ( 1,  1)]

def get_screen():
    pyautogui.keyDown('winleft')
    pyautogui.press('down', presses=3, interval=0.5)
    pyautogui.keyUp('winleft')
    time.sleep(1)
    screenshoot = pyautogui.screenshot()
    screenshoot = cv2.cvtColor(np.array(screenshoot), cv2.COLOR_RGB2BGR)
    return screenshoot
def recognize_board(screenshoot):
    board = cv2.imread('gamewindow.png')
    result = cv2.matchTemplate(screenshoot, board, cv2.TM_CCOEFF_NORMED)
    
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    boardCoordinates = [(int(max_loc[0]), int(max_loc[1])), 
                        (max_loc[0] + board.shape[1], max_loc[1] + board.shape[0])]
    return boardCoordinates
def next_board():
    screenshoot = pyautogui.screenshot()
    screenshoot = cv2.cvtColor(np.array(screenshoot), cv2.COLOR_RGB2BGR)
    return screenshoot
def click_on_board(x, y):
    pyautogui.click(x, y)
    pyautogui.moveTo(x+400, y)
def right_click_on_board(x, y):
    pyautogui.click(x, y, button='right')
    pyautogui.moveTo(x+400, y)
def get_cells_coordinates(boardCoordinates):
    start_x, start_y = boardCoordinates[0]
    end_x, end_y = boardCoordinates[1]
    width = end_x - start_x
    height = end_y - start_y
    cell_size = 16
    rows = height // cell_size
    cols = width // cell_size
    

    cells = []
    for i in range(rows):
        for j in range(cols):
            start_x_cell = j * cell_size + start_x
            start_y_cell = i * cell_size + start_y
            end_x_cell = cell_size + start_x_cell
            end_y_cell = cell_size + start_y_cell
            cellCoordinates = [(start_x_cell, start_y_cell), (end_x_cell, end_y_cell)]
            cells.append(cellCoordinates)
        
    return cells 
def detect_cell_value(cell_image):

    hsv = cv2.cvtColor(cell_image, cv2.COLOR_BGR2HSV)
    
    white_mask = cv2.inRange(hsv, (0, 0, 200), (180, 25, 255))  # Partes blancas (jugable)
    gray_mask = cv2.inRange(hsv, (0, 0, 50), (180, 20, 100))    # Gris (vacía)
    blue_mask = cv2.inRange(hsv, (100, 150, 0), (140, 255, 255)) # Azul (1 bomba)
    green_mask = cv2.inRange(hsv, (40, 100, 50), (80, 255, 255)) # Verde (2 bombas)
    red_mask = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))  # Rojo (3 bombas)
    navy_mask = cv2.inRange(hsv, (110, 50, 50), (130, 255, 255)) # Azul oscuro (4 bombas)
    black_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 30))    # Negro (bomba)
    
   
    white_pixels = cv2.countNonZero(white_mask)
    gray_pixels = cv2.countNonZero(gray_mask)
    blue_pixels = cv2.countNonZero(blue_mask)
    green_pixels = cv2.countNonZero(green_mask)
    red_pixels = cv2.countNonZero(red_mask)
    navy_pixels = cv2.countNonZero(navy_mask)
    black_pixels = cv2.countNonZero(black_mask)
    
    if gray_pixels > 200:
        return "E"
    elif white_pixels > 30 and white_pixels < 100 and not(red_pixels > 10 and black_pixels > 10):
        return "P"
    elif white_pixels > 100:
        return "0"
    elif red_pixels > 10 and black_pixels > 10:
        return "F"
    elif blue_pixels > 30:
        return "1"  # 1 bomba
    elif green_pixels > 30:
        return "2"  # 2 bombas
    elif red_pixels > 30:
        return "3"  # 3 bombas
    elif navy_pixels > 40:
        return "4"  # 4 bombas
    elif black_pixels > 50:
        return "B"
    return "E"  # Desconocido
def get_cells_values(cells, screenshot):
    cell_values = []
    for cell_coords in cells:
        x1, y1 = cell_coords[0]
        x2, y2 = cell_coords[1]
        
        # Extrae la imagen de la celda específica
        cell_image = screenshot[y1:y2, x1:x2]
        cell_value = detect_cell_value(cell_image)
        cell_values.append(cell_value)
    
    return cell_values
def print_board(cell_values, rows, cols):
    board = ""
    for i in range(rows):
        # Selecciona los valores de la fila actual
        row = cell_values[i * cols: (i + 1) * cols]
        # Formatea la fila con espacio entre los valores
        board += " | ".join(row) + "\n"
        # Línea separadora para mejorar la visualización
        board += "- " * (cols * 2) + "\n"  # Ajustar el número de guiones según sea necesario
    
    print("Minesweeper Board:")
    print(board)
def cell_value_matrix(cell_values, rows, cols):
    matrix = []
    for i in range(rows):
        matrix.append(cell_values[i * cols: (i + 1) * cols])
    return matrix
def get_secure_bombs(matrix, rows, cols):
    bombs = []
    
    # Las 8 posiciones adyacentes a la celda actual.
    conditions = {
    "1": [(1, 0)],
    "2": [(2, 0), (1, 1)],
    "3": [(3, 0), (1, 2), (2, 1)],
    "4": [(4, 0), (1, 3), (2, 2), (3, 1)],
    }

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] in "1234":

                free_actual_cells = []
                flagged_actual_cells = []

                for df, dc in possible_movements:
                    r_ad, c_ad = i + df, j + dc
                    if 0 <= r_ad < rows and 0 <= c_ad < cols:
                        if matrix[r_ad][c_ad] == "P":
                            free_actual_cells.append((r_ad, c_ad))
                        if matrix[r_ad][c_ad] == "F":
                            flagged_actual_cells.append((r_ad, c_ad))
                

                # Guarda el valor de la celda actual.
                current_value = matrix[i][j]
                if current_value in conditions:
                    for free_count, flagged_count in conditions[current_value]:
                        if len(free_actual_cells) == free_count and len(flagged_actual_cells) == flagged_count:
                            bombs.append(free_actual_cells)
                            
    bombs_aplaned = [tupla for sublist in bombs for tupla in sublist]
    secured_bombs_index = list(set(bombs_aplaned))

    return secured_bombs_index
def get_save_movements(matrix, rows, cols):
    save = []

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] in "1234":

                free_actual_cells = []
                flagged_actual_cells = []
                for df, dc in possible_movements:
                    r_ad, c_ad = i + df, j + dc
                    if 0 <= r_ad < rows and 0 <= c_ad < cols:
                        if matrix[r_ad][c_ad] == "P":
                            free_actual_cells.append((r_ad, c_ad))
                        if matrix[r_ad][c_ad] == "F":
                            flagged_actual_cells.append((r_ad, c_ad))
                
                if matrix[i][j] == "1" and len(flagged_actual_cells) == 1:
                    save.append(free_actual_cells)
                if matrix[i][j] == "2" and len(flagged_actual_cells) == 2:
                    save.append(free_actual_cells)
                if matrix[i][j] == "3" and len(flagged_actual_cells) == 3:
                    save.append(free_actual_cells)
                if matrix[i][j] == "4" and len(flagged_actual_cells) == 4:
                    save.append(free_actual_cells)
                            
    saves_aplaned = [tupla for sublist in save for tupla in sublist]
    secured_saves_index = list(set(saves_aplaned))

    return secured_saves_index
def solve_minesweeper(rows, cols):
    gameCoordinates = recognize_board(get_screen())
    boardCoordinates = [(gameCoordinates[0][0] + 10, gameCoordinates[0][1] + 50), 
                        (gameCoordinates[1][0] - 5, gameCoordinates[1][1])]
    cells = get_cells_coordinates(boardCoordinates)
    gameState = True

    while gameState:
        screenshot = next_board()
        cell_values = get_cells_values(cells, screenshot)
        
        print_board(cell_values, rows, cols)

        matrix = cell_value_matrix(cell_values, rows, cols)

        save_movements = get_save_movements(matrix, rows, cols)
        secure_bombs = get_secure_bombs(matrix, rows, cols)

        if cell_values.count("B") >= 1:
            gameState = False
            print("GAME OVER: BOOM!")

        if cell_values.count("0") >= 1:
            gameState = False
            print("YOU WIN!")

        if cell_values.count("P") >= 70:
            random_cell = random.choice(cells)
            x1, y1= random_cell[0][0], random_cell[0][1]
            x2, y2= random_cell[1][0], random_cell[1][1]

            x = (x1 + x2) // 2
            y = (y1 + y2) // 2

            click_on_board(x, y)
        elif len(secure_bombs) > 0:
            for bomb in secure_bombs:
                print(bomb)
                x1, y1= cells[bomb[0]*rows + bomb[1]][0][0], cells[bomb[0]*rows + bomb[1]][0][1]
                x2, y2= cells[bomb[0]*rows + bomb[1]][1][0], cells[bomb[0]*rows + bomb[1]][1][1]

                x = (x1 + x2) // 2
                y = (y1 + y2) // 2
                right_click_on_board(x, y)
        elif len(save_movements) > 0:
            for save in save_movements:
                print(save)
                x1, y1= cells[save[0]*rows + save[1]][0][0], cells[save[0]*rows + save[1]][0][1]
                x2, y2= cells[save[0]*rows + save[1]][1][0], cells[save[0]*rows + save[1]][1][1]

                x = (x1 + x2) // 2
                y = (y1 + y2) // 2
                click_on_board(x, y)
        elif cell_values.count("P") >= 1:
            random_cell = random.choice(cells)
            x1, y1= random_cell[0][0], random_cell[0][1]
            x2, y2= random_cell[1][0], random_cell[1][1]

            x = (x1 + x2) // 2
            y = (y1 + y2) // 2

            click_on_board(x, y)
        else:
            gameState = False
            print("GAME OVER, NO HAY MOVIMIENTOS POSIBLES")
solve_minesweeper(9, 9)