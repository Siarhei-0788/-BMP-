import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import os
import struct
import binascii

def center_window(root, width=900, height=700):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

def show_image():
    global img
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для отображения!")
        return
    image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = image.resize((600, 500))
    image = ImageTk.PhotoImage(image)
    panel.config(image=image)
    panel.image = image

def open_image():
    global img, img_path
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.bmp;*.png;*.jpg;*.jpeg;*.psa")])
    if not file_path or not os.path.exists(file_path):
        messagebox.showerror("Ошибка", "Файл не найден!")
        return

    img_path = file_path
    try:
        if file_path.lower().endswith('.psa'):
            with open(file_path, "rb") as f:
                header = f.read(16)
                signature, width, height, channels = struct.unpack('<4sIII', header)
                if signature.strip() != b'PSA':
                    messagebox.showerror("Ошибка", "Неверный формат файла PSA!")
                    return
                img_data = np.frombuffer(f.read(), dtype=np.uint8)
                img = img_data.reshape((height, width, channels))
        else:
            img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    except Exception as e:
        messagebox.showerror("Ошибка загрузки!", f"Не удалось загрузить изображение.\n{e}")
        return

    if img is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить изображение! Проверьте формат файла.")
        return

    show_image()

def save_image():
    global img, img_path
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для сохранения!")
        return

    if not img_path:
        messagebox.showerror("Ошибка", "Путь к файлу неизвестен!")
        return

    try:
        folder = os.path.dirname(img_path)
        filename = os.path.basename(img_path)
        save_path = os.path.normpath(os.path.join(folder, f"edited_{filename}"))
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        if img.dtype != np.uint8:
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)
        
        ext = os.path.splitext(save_path)[1].lower()
        ret, buf = cv2.imencode(ext, img)
        
        if ret:
            with open(save_path, 'wb') as f:
                f.write(buf)
            messagebox.showinfo("Успех", f"Изображение сохранено как:\n{save_path}")
        else:
            messagebox.showerror("Ошибка", "Не удалось закодировать изображение!")
            
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{str(e)}")

def save_image_as():
    global img, img_path
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для сохранения!")
        return

    try:
        initial_dir = os.path.dirname(img_path) if img_path else os.getcwd()
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".png",
            filetypes=[
                ("PNG Files", "*.png"),
                ("JPEG Files", "*.jpg"),
                ("BMP Files", "*.bmp"),
                ("PSA Files", "*.psa"),
                ("All Files", "*.*")
            ])
        
        if not file_path:
            return

        file_path = os.path.normpath(file_path)
        
        if img.dtype != np.uint8:
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)
        
        if file_path.lower().endswith('.psa'):
            height, width, channels = img.shape
            header = struct.pack('<4sIII', b'PSA ', width, height, channels)
            with open(file_path, "wb") as f:
                f.write(header)
                f.write(img.tobytes())
        else:
            ext = os.path.splitext(file_path)[1].lower()
            ret, buf = cv2.imencode(ext, img)
            
            if ret:
                with open(file_path, 'wb') as f:
                    f.write(buf)
            else:
                messagebox.showerror("Ошибка", f"Не удалось сохранить в формате {ext}")
                return
        
        img_path = file_path
        messagebox.showinfo("Успех", f"Файл успешно сохранён!\nФайл: {file_path}")
            
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{str(e)}")

def read_image_header(file_path):
    """Чтение заголовка графического файла"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    ext = os.path.splitext(file_path)[1].lower()
    header_info = {'Формат': ext[1:].upper()}
    
    try:
        with open(file_path, 'rb') as f:
            if ext == '.bmp':
                header = f.read(54)
                header_info.update({
                    'Сигнатура': header[:2].decode('ascii'),
                    'Размер файла': f"{struct.unpack('<I', header[2:6])[0]} байт",
                    'Смещение данных': f"{struct.unpack('<I', header[10:14])[0]} байт",
                    'Ширина': f"{struct.unpack('<i', header[18:22])[0]} пикселей",
                    'Высота': f"{struct.unpack('<i', header[22:26])[0]} пикселей",
                    'Бит на пиксель': struct.unpack('<H', header[28:30])[0],
                    'Тип сжатия': struct.unpack('<I', header[30:34])[0]
                })
            elif ext == '.psa':
                header = f.read(16)
                header_info.update({
                    'Сигнатура': header[:4].decode('ascii').strip(),
                    'Ширина': f"{struct.unpack('<I', header[4:8])[0]} пикселей",
                    'Высота': f"{struct.unpack('<I', header[8:12])[0]} пикселей",
                    'Каналы': struct.unpack('<I', header[12:16])[0]
                })
            else:
                header_info['Информация'] = "Просмотр заголовка доступен только для BMP и PSA"
    except Exception as e:
        header_info['Ошибка'] = f"Не удалось прочитать заголовок: {str(e)}"
    
    return header_info

def show_header_info():
    global img_path
    if not img_path:
        messagebox.showerror("Ошибка", "Файл не загружен!")
        return
    
    header_info = read_image_header(img_path)
    if not header_info:
        messagebox.showerror("Ошибка", "Не удалось прочитать файл!")
        return
    
    header_window = tk.Toplevel()
    header_window.title(f"Заголовок файла: {os.path.basename(img_path)}")
    header_window.geometry("500x400")
    
    notebook = ttk.Notebook(header_window)
    notebook.pack(fill='both', expand=True)
    
    # Вкладка с таблицей
    table_frame = ttk.Frame(notebook)
    notebook.add(table_frame, text="Таблица")
    
    canvas = tk.Canvas(table_frame)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    for i, (key, value) in enumerate(header_info.items()):
        tk.Label(scrollable_frame, text=key, anchor="w", width=25).grid(row=i, column=0, sticky="ew", padx=5, pady=2)
        tk.Label(scrollable_frame, text=value, anchor="w", width=25).grid(row=i, column=1, sticky="ew", padx=5, pady=2)
    
    # Вкладка с HEX-представлением
    hex_frame = ttk.Frame(notebook)
    notebook.add(hex_frame, text="HEX")
    
    hex_text = tk.Text(hex_frame, wrap="none", font=("Courier", 10))
    scroll_y = ttk.Scrollbar(hex_frame, orient="vertical", command=hex_text.yview)
    scroll_x = ttk.Scrollbar(hex_frame, orient="horizontal", command=hex_text.xview)
    hex_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    
    try:
        with open(img_path, 'rb') as f:
            header = f.read(128)  # Читаем первые 128 байт
            hex_text.insert("end", binascii.hexlify(header, ' ', 1).decode('ascii'))
    except Exception as e:
        hex_text.insert("end", f"Ошибка чтения файла: {str(e)}")
    
    hex_text.configure(state="disabled")
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    hex_text.pack(side="left", fill="both", expand=True)
    
    ttk.Button(header_window, text="Закрыть", command=header_window.destroy).pack(pady=10)

def extract_metadata(image_path):
    """Извлечение метаданных из изображения"""
    metadata = {
        "Автор файла": "Неизвестный",
        "Название программы": "Графический редактор",
        "Геоданные": "Не доступны",
        "Камера": "Неизвестная"
    }
    
    if image_path.lower().endswith((".jpg", ".jpeg")):
        try:
            img_pil = Image.open(image_path)
            exif_data = img_pil._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = Image.ExifTags.TAGS.get(tag, tag)
                    if tag_name == "Make":
                        metadata["Камера"] = value
                    elif tag_name == "Model":
                        metadata["Камера"] += f" {value}"
                    elif tag_name == "GPSInfo":
                        metadata["Геоданные"] = str(value)
        except Exception as e:
            print(f"Ошибка извлечения EXIF: {e}")
    
    return metadata

def generate_report():
    global img, img_path
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для анализа!")
        return

    height, width, channels = img.shape
    avg_color = np.mean(img, axis=(0, 1)).astype(int)
    metadata = extract_metadata(img_path)
    file_ext = os.path.splitext(img_path)[-1][1:].upper() if img_path else "N/A"

    report_window = tk.Toplevel()
    report_window.title("Отчет об изображении")
    report_window.geometry("600x500")
    
    notebook = ttk.Notebook(report_window)
    notebook.pack(fill='both', expand=True)
    
    # Основная информация
    main_frame = ttk.Frame(notebook)
    notebook.add(main_frame, text="Основная информация")
    
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    data = [
        ("Название программы", metadata['Название программы']),
        ("Тип файла", file_ext),
        ("Автор файла", metadata['Автор файла']),
        ("Размер заголовка", "54 байт (BMP)" if file_ext == "BMP" else "N/A"),
        ("Размер изображения", f"{width} × {height} пикселей"),
        ("Ширина", f"{width} пикселей"),
        ("Высота", f"{height} пикселей"),
        ("Средний цвет (RGB)", f"({avg_color[0]}, {avg_color[1]}, {avg_color[2]})"),
        ("Глубина цвета", f"{channels * 8}-бит"),
        ("Камера", metadata['Камера']),
        ("Геоданные", metadata['Геоданные'])
    ]
    
    for i, (param, value) in enumerate(data):
        tk.Label(scrollable_frame, text=param, anchor="w", width=25).grid(row=i, column=0, sticky="ew", padx=5, pady=2)
        tk.Label(scrollable_frame, text=value, anchor="w", width=25).grid(row=i, column=1, sticky="ew", padx=5, pady=2)
    
    # Заголовок файла
    if file_ext in ("BMP", "PSA"):
        header_frame = ttk.Frame(notebook)
        notebook.add(header_frame, text="Заголовок файла")
        
        header_info = read_image_header(img_path)
        if header_info:
            canvas = tk.Canvas(header_frame)
            scrollbar = ttk.Scrollbar(header_frame, orient="vertical", command=canvas.yview)
            scrollable_header_frame = ttk.Frame(canvas)
            
            scrollable_header_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_header_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            for i, (key, value) in enumerate(header_info.items()):
                tk.Label(scrollable_header_frame, text=key, anchor="w", width=25).grid(row=i, column=0, sticky="ew", padx=5, pady=2)
                tk.Label(scrollable_header_frame, text=value, anchor="w", width=25).grid(row=i, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Button(report_window, text="Закрыть", command=report_window.destroy).pack(pady=10)

def add_noise():
    global img
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для обработки!")
        return

    noise_level = simpledialog.askfloat("Шум", "Введите процент шума (0-100):", minvalue=0, maxvalue=100)
    if noise_level is not None:
        noisy_img = img.copy()
        num_noise = int(noise_level / 100 * noisy_img.size / 3)
        coords = [np.random.randint(0, i - 1, num_noise) for i in noisy_img.shape[:2]]
        noisy_img[coords[0], coords[1], :] = 255
        coords = [np.random.randint(0, i - 1, num_noise) for i in noisy_img.shape[:2]]
        noisy_img[coords[0], coords[1], :] = 0
        img[:] = noisy_img[:]
        show_image()

def apply_median_filter():
    global img
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для обработки!")
        return

    img = cv2.medianBlur(img, 5)
    show_image()

import numpy as np
import cv2
import tkinter as tk
from tkinter import messagebox, simpledialog

def apply_laplacian():
    global img
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для обработки!")
        return
    
    try:
        # Запрос порога у пользователя
        threshold_value = simpledialog.askinteger("Настройка порога", 
                                                  "Введите значение порога (0-255):", 
                                                  minvalue=0, maxvalue=255)
        if threshold_value is None:
            return  # Если пользователь отменил ввод

        # Ядро Лапласа H15
        kernel = np.array([[1, -2, 1],
                           [-2, 4, -2],
                           [1, -2, 1]], dtype=np.float32)
        
        # Конвертируем в оттенки серого, если изображение цветное
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Применяем свёртку с ядром Лапласа
        laplacian = cv2.filter2D(gray, cv2.CV_64F, kernel)
        
        # Нормализуем результат и преобразуем в 8-битный формат
        laplacian = np.absolute(laplacian)
        laplacian = np.uint8(255 * laplacian / np.max(laplacian))
        
        # Создаем контурное изображение с заданным порогом
        _, contours = cv2.threshold(laplacian, threshold_value, 255, cv2.THRESH_BINARY_INV)
        
        # Для цветного отображения преобразуем обратно в BGR
        if len(img.shape) == 3:
            contours = cv2.cvtColor(contours, cv2.COLOR_GRAY2BGR)
        
        # Сохраняем результат
        img = contours.copy()
        
        show_image()
        messagebox.showinfo("Успех", f"Контурное изображение получено с порогом {threshold_value}")
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось применить оператор Лапласа:\n{str(e)}")

def stretch_height():
    global img
    if img is None:
        messagebox.showerror("Ошибка", "Нет изображения для обработки!")
        return

    M = simpledialog.askinteger("Растяжение", "Введите коэффициент увеличения высоты (1-10):", minvalue=1, maxvalue=10)
    if M is None or M < 1:
        return

    height, width = img.shape[:2]
    new_height = int(height * M)

    try:
        img_resized = cv2.resize(img, (width, new_height), interpolation=cv2.INTER_CUBIC)
        if img_resized.shape[0] == new_height:
            img = img_resized.copy()
            show_image()
        else:
            messagebox.showerror("Ошибка", "Растяжение изображения не удалось!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось изменить высоту: {e}")

def exit_app():
    root.quit()

# Создание главного окна
root = tk.Tk()
root.title("GE-BMP (Графический редактор для формата BMP)")
center_window(root, 900, 700)

# Главное меню
menu_bar = tk.Menu(root)

# Меню "Файл"
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Открыть", command=open_image)
file_menu.add_command(label="Сохранить", command=save_image)
file_menu.add_command(label="Сохранить как...", command=save_image_as)
file_menu.add_separator()
file_menu.add_command(label="Просмотр заголовка", command=show_header_info)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=exit_app)
menu_bar.add_cascade(label="Файл", menu=file_menu)

# Меню "Обработка"
process_menu = tk.Menu(menu_bar, tearoff=0)
process_menu.add_command(label="Добавить шум", command=add_noise)
process_menu.add_command(label="Медианный фильтр", command=apply_median_filter)
process_menu.add_command(label="Оператор Лапласа", command=apply_laplacian)
process_menu.add_command(label="Растяжение по высоте", command=stretch_height)
menu_bar.add_cascade(label="Обработка", menu=process_menu)

# Меню "Отчет"
report_menu = tk.Menu(menu_bar, tearoff=0)
report_menu.add_command(label="Создать отчет", command=generate_report)
menu_bar.add_cascade(label="Отчет", menu=report_menu)

root.config(menu=menu_bar)

# Панель для отображения изображения
panel = tk.Label(root)
panel.pack()

# Информация о разработчике
footer = tk.Label(root, text="Разработчик: Пачко С.А. | АС-576", font=("Arial", 10), fg="gray")
footer.pack(side=tk.BOTTOM, pady=5)

# Глобальные переменные
img = None
img_path = None

root.mainloop()