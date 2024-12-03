import cv2
import pytesseract
from PIL import Image
import numpy as np

def solve_sudoku_board(board):
    """Solve the Sudoku puzzle using backtracking."""
    empty = find_empty(board)
    if not empty:
        return board  # Return the solved board
    row, col = empty

    for num in range(1, 10):
        if valid(board, num, (row, col)):
            board[row][col] = num
            if solve_sudoku_board(board):
                return board
            board[row][col] = 0  # Reset on backtrack

    return None  # No solution found

def valid(board, num, pos):
    """Check if a number can be placed at the given position."""
    row, col = pos
    # Check row and column
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False

    # Check 3x3 box
    box_x = col // 3
    box_y = row // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if board[i][j] == num:
                return False

    return True

def find_empty(board):
    """Find an empty space in the board (0 represents empty)."""
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)  # row, col
    return None

def image_to_sudoku_board(image):
    """Convert the uploaded image to a Sudoku board."""
    image = image.convert('L')  # Convert to grayscale
    image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize the image

    # Use pytesseract to extract text, ensuring digits are captured correctly
    data = pytesseract.image_to_string(image, config='--psm 6 outputbase digits')

    lines = data.splitlines()
    board = []
    for line in lines:
        if line.strip():
            # Split line into individual numbers and handle any non-digit characters
            row = [int(num) if num.isdigit() else 0 for num in line.split()]
            board.append(row)

    # Ensure the board is always 9x9
    while len(board) < 9:
        board.append([0] * 9)
    
    for i in range(9):
        if len(board[i]) < 9:
            board[i] += [0] * (9 - len(board[i]))

    return board

def solve_sudoku(input_image_path, output_image_path):
    """Main function to read an image, solve the Sudoku, and save the output image."""
    img = cv2.imread(input_image_path)
    pil_img = Image.open(input_image_path)

    # Convert the image to a Sudoku board
    board = image_to_sudoku_board(pil_img)

    # Solve the Sudoku board
    solved_board = solve_sudoku_board(board)

    # Visualize the solved board on the image
    solved_img = visualize_sudoku_on_image(img, solved_board)

    # Save the output image
    cv2.imwrite(output_image_path, solved_img)

def visualize_sudoku_on_image(img, board):
    """Visualize the solved Sudoku on the image."""
    cell_size = 50  # Adjust based on image size and grid scaling
    font = cv2.FONT_HERSHEY_SIMPLEX
    solved_img = img.copy()

    for i in range(9):
        for j in range(9):
            top_left = (j * cell_size, i * cell_size)
            bottom_right = ((j + 1) * cell_size, (i + 1) * cell_size)
            cv2.rectangle(solved_img, top_left, bottom_right, (0, 0, 0), 2)

            if board[i][j] != 0:
                # Draw the solved number in the corresponding cell
                cv2.putText(solved_img, str(board[i][j]), 
                            (top_left[0] + 15, top_left[1] + 35), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    return solved_img

def preprocess_image_for_ocr(input_image_path):
    """Preprocess the image for better OCR accuracy."""
    img = cv2.imread(input_image_path)
    # Convert the image to grayscale for better OCR accuracy
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding to get better binarization for OCR
    thresh_img = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)

    # Optionally apply median blur to reduce noise
    blurred_img = cv2.medianBlur(thresh_img, 3)

    return Image.fromarray(blurred_img)  # Convert back to PIL Image

def image_to_sudoku_board_with_preprocessing(input_image_path):
    """Convert the uploaded image to a Sudoku board with preprocessing."""
    pil_img = preprocess_image_for_ocr(input_image_path)
    return image_to_sudoku_board(pil_img)
