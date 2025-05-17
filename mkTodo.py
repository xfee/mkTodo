import tkinter as tk
from tkinter import ttk, simpledialog
import json
import os
import ctypes
import sys

class mkTodo:
    def __init__(self, root):
        self.root = root
        self.root.title("mkTodo - 秒开待办")
        self.root.geometry("450x600")
        
       
        # 设置主题样式
        self.style = ttk.Style()
        self.style.configure("Custom.TEntry", padding=10)
        self.style.configure("TodoItem.TCheckbutton", padding=5)
        
        # 设置窗口背景色
        self.root.configure(bg="#F5F5F5")
        
        # 数据存储
        self.todos = []
        self.load_todos()
        
        # 拖动提示线
        self.drag_line = None
        
        # 是否在待办事项前添加时间前缀
        self.add_time_prefix = True

        # 创建界面
        self.create_widgets()
        
        # 初始化hover状态
        self.current_hover_item = None 
        
    def create_widgets(self):
        # 输入框容器
        input_frame = tk.Frame(self.root, bg="#F5F5F5")
        input_frame.pack(pady=(20,10), padx=20, fill="x")
        
        # 输入框
        self.todo_entry = ttk.Entry(
            input_frame,
            font=("Microsoft YaHei UI", 10),
            style="Custom.TEntry"
        )
        self.todo_entry.pack(fill="x")
        self.todo_entry.bind('<Return>', lambda e: self.add_todo())
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0, font=("Microsoft YaHei UI", 9))
        self.context_menu.add_command(label="编辑", command=self.edit_selected)
        self.context_menu.add_command(label="删除", command=self.delete_selected)
        
        # 创建列表框架
        list_frame = tk.Frame(self.root, bg="white", bd=1, relief="solid")
        list_frame.pack(pady=(0,20), padx=20, fill="both", expand=True)
        
        # 待办事项列表
        self.todo_listbox = tk.Listbox(
            list_frame,
            font=("Microsoft YaHei UI", 10),  
            selectmode=tk.SINGLE,
            activestyle='none',
            bd=0,
            highlightthickness=0,
            selectbackground="#E6F3FF",
            selectforeground="#000000",
            bg="white"
        )
        self.todo_listbox.pack(fill="both", expand=True, padx=1, pady=1)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.todo_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.todo_listbox.configure(yscrollcommand=self._on_scroll)
        self.scrollbar = scrollbar  # 保存滚动条引用
        
        # 绑定点击事件
        self.todo_listbox.bind('<Double-Button-1>', self.on_double_click)
        self.todo_listbox.bind('<Button-3>', self.show_context_menu)
        
        # 绑定拖动事件
        self.todo_listbox.bind('<Button-1>', self.on_drag_start)
        self.todo_listbox.bind('<B1-Motion>', self.on_drag_motion)
        self.todo_listbox.bind('<ButtonRelease-1>', self.on_drag_release)
        
        # 绑定鼠标悬停事件
        self.todo_listbox.bind('<Enter>', self.on_listbox_enter)
        self.todo_listbox.bind('<Leave>', self.on_listbox_leave)
        self.todo_listbox.bind('<Motion>', self.on_item_hover)
        
        # 记录当前悬停的项目
        self.current_hover_item = None
        
        # 更新列表显示
        self.update_listbox()
        
        # 设置输入框提示
        self.todo_entry.insert(0, "添加待办事项...")
        self.todo_entry.bind('<FocusIn>', self.on_entry_click)
        self.todo_entry.bind('<FocusOut>', self.on_entry_focusout)
        
    def on_entry_click(self, event):
        if self.todo_entry.get() == "添加待办事项...":
            self.todo_entry.delete(0, tk.END)
            self.todo_entry.configure(foreground="black")
            
    def on_entry_focusout(self, event):
        if self.todo_entry.get() == "":
            self.todo_entry.insert(0, "添加待办事项...")
            self.todo_entry.configure(foreground="gray")
            
    def add_todo(self):
        todo = self.todo_entry.get().strip()
        if todo and todo != "添加待办事项...":
            if self.add_time_prefix:
                # 获取当前时间并格式化为MMDD格式
                from datetime import datetime
                current_time = datetime.now()
                time_prefix = current_time.strftime("%m%d")
                # 在待办事项前添加时间前缀
                todo_with_time = f"{time_prefix} - {todo}"
                self.todos.insert(0, {"text": todo_with_time, "completed": False})
            else:
                self.todos.insert(0, {"text": todo, "completed": False})
            self.todo_entry.delete(0, tk.END)
            # 由于焦点还在输入框，不需要显示提示文字
            self.todo_entry.configure(foreground="black")
            self.save_todos()
            self.update_listbox()
            
    def on_double_click(self, event):
        # 获取点击位置对应的项目索引
        index = self.todo_listbox.nearest(event.y)
        if 0 <= index < self.todo_listbox.size():
            # 获取项目的边界框
            bbox = self.todo_listbox.bbox(index)
            if bbox and bbox[1] <= event.y <= bbox[1] + bbox[3]:
                self.toggle_complete()
                
    def toggle_complete(self):
        selection = self.todo_listbox.curselection()
        if selection:
            index = selection[0]
            self.todos[index]["completed"] = not self.todos[index]["completed"]
            self.save_todos()
            self.update_listbox()
            
    def show_context_menu(self, event):
        # 获取鼠标点击位置对应的项目
        index = self.todo_listbox.nearest(event.y)
        if 0 <= index < self.todo_listbox.size():
            # 获取项目的边界框
            bbox = self.todo_listbox.bbox(index)
            if bbox and bbox[1] <= event.y <= bbox[1] + bbox[3]:
                # 选中被点击的项目
                self.todo_listbox.selection_clear(0, tk.END)
                self.todo_listbox.selection_set(index)
                # 记录当前选中的索引
                self.selected_index = index
                # 在鼠标位置显示菜单
                self.context_menu.post(event.x_root, event.y_root)
            
    def delete_selected(self):
        if hasattr(self, 'selected_index'):
            # 清除hover状态
            if hasattr(self, 'current_hover_item'):
                delattr(self, 'current_hover_item')
            # 删除项目
            self.todos.pop(self.selected_index)
            self.save_todos()
            self.update_listbox()
            
    def edit_selected(self):
        if hasattr(self, 'selected_index'):
            current_text = self.todos[self.selected_index]["text"]
            new_text = simpledialog.askstring("编辑待办事项", 
                                            "修改内容:",
                                            initialvalue=current_text,
                                            parent=self.root)
            if new_text and new_text.strip():
                self.todos[self.selected_index]["text"] = new_text.strip()
                self.save_todos()
                self.update_listbox()
                
    def on_drag_start(self, event):
        # 获取点击位置对应的项目索引
        index = self.todo_listbox.nearest(event.y)
        if 0 <= index < self.todo_listbox.size():
            # 获取项目的边界框
            bbox = self.todo_listbox.bbox(index)
            if bbox:
                # 只有当点击在项目的实际区域内时才处理
                if bbox[1] <= event.y <= bbox[1] + bbox[3]:
                    self.drag_start_index = index
                    # 选中被拖动的项目
                    self.todo_listbox.selection_clear(0, tk.END)
                    self.todo_listbox.selection_set(self.drag_start_index)
                    # 记录原始背景色
                    self.original_bg = self.todo_listbox.itemcget(self.drag_start_index, "background")
                    # 设置拖动时的背景色
                    self.todo_listbox.itemconfig(self.drag_start_index, background="#E3F2FD")
                    
    def on_drag_motion(self, event):
        if hasattr(self, 'drag_start_index'):
            # 获取当前鼠标位置对应的索引
            current_index = self.todo_listbox.nearest(event.y)
            if current_index >= 0 and current_index != self.drag_start_index:
                # 计算插入位置
                bbox = self.todo_listbox.bbox(current_index)
                if bbox:
                    # 如果鼠标在项目的下半部分，插入点在下方
                    if event.y > bbox[1] + bbox[3] // 2:
                        current_index += 1
                        
                    # 移动项目
                    item = self.todos.pop(self.drag_start_index)
                    self.todos.insert(current_index if current_index < self.drag_start_index else current_index - 1, item)
                    
                    # 更新显示
                    self.update_listbox()
                    
                    # 更新拖动索引和选中状态
                    self.drag_start_index = current_index if current_index < self.drag_start_index else current_index - 1
                    self.todo_listbox.selection_clear(0, tk.END)
                    self.todo_listbox.selection_set(self.drag_start_index)
                    # 设置拖动时的背景色
                    self.todo_listbox.itemconfig(self.drag_start_index, background="#E3F2FD")
                
    def on_drag_release(self, event):
        if hasattr(self, 'drag_start_index'):
            # 恢复原始背景色
            self.todo_listbox.itemconfig(self.drag_start_index, background=self.original_bg)
            # 保存更改
            self.save_todos()
            # 清除拖动状态
            delattr(self, 'drag_start_index')
            
    def _on_scroll(self, *args):
        # 检查是否需要显示滚动条
        if self.todo_listbox.yview() == (0.0, 1.0):
            self.scrollbar.pack_forget()  # 隐藏滚动条
        else:
            self.scrollbar.pack(side="right", fill="y")  # 显示滚动条
        self.scrollbar.set(*args)  # 更新滚动条位置
        
    def update_listbox(self):
        self.todo_listbox.delete(0, tk.END)
        for todo in self.todos:
            checkbox = "☑" if todo["completed"] else "☐"
            text = todo["text"]
            # 在每个项目上下添加一点空白
            display_text = f" {checkbox}  {text} "
            self.todo_listbox.insert(tk.END, display_text)
            # 设置已完成项目的颜色
            if todo["completed"]:
                self.todo_listbox.itemconfig(tk.END, fg="#888888")
            
    def save_todos(self):
        with open("mkTodo.json", "w", encoding="utf-8") as f:
            json.dump(self.todos, f, ensure_ascii=False)
            
    def load_todos(self):
        try:
            with open("mkTodo.json", "r", encoding="utf-8") as f:
                self.todos = json.load(f)
        except FileNotFoundError:
            self.todos = []
            
    def on_listbox_enter(self, event):
        # 鼠标进入列表框时，更新当前项目
        self.on_item_hover(event)
        
    def on_listbox_leave(self, event):
        # 清除hover状态
        if self.current_hover_item is not None:
            try:
                if 0 <= self.current_hover_item < self.todo_listbox.size():
                    self.todo_listbox.itemconfig(self.current_hover_item, background="white")
            except tk.TclError:
                pass  # 忽略可能的错误
        self.current_hover_item = None
            
    def on_item_hover(self, event):
        try:
            # 获取鼠标下的项目索引
            index = self.todo_listbox.nearest(event.y)
            if index >= 0:
                # 如果鼠标移动到新的项目上
                if index != self.current_hover_item:
                    # 清除旧项目的高亮
                    if self.current_hover_item is not None:
                        if 0 <= self.current_hover_item < self.todo_listbox.size():
                            self.todo_listbox.itemconfig(self.current_hover_item, background="white")
                    
                    # 设置新项目的高亮
                    self.todo_listbox.itemconfig(index, background="#F5F5F5")
                    self.current_hover_item = index
        except tk.TclError:
            pass  # 忽略可能的错误

if __name__ == "__main__":
    import sys
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe运行
        import os
        os.environ['PYTHONOPTIMIZE'] = '1'  # 优化Python运行时
        
    root = tk.Tk()
    root.withdraw()  # 先隐藏窗口
    

    
    # 设置应用ID (必须在创建任何窗口之前)
    myappid = 'mkTodo.todolist.1.0'  # 任意字符串，但需要唯一
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # 设置图标路径
    icon_path = 'images/favicon.ico'
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe，使用相对于exe的路径
        base_dir = os.path.dirname(sys.executable)
        # 尝试多个可能的图标路径
        possible_paths = [
            os.path.join(base_dir, 'images', 'favicon.ico'),
            os.path.join(base_dir, '_internal', 'images', 'favicon.ico')
        ]
        
        # 使用第一个存在的路径
        for path in possible_paths:
            if os.path.exists(path):
                icon_path = path
                print(f"找到图标文件: {path}")
                break
        
    # 确保图标文件存在
    if os.path.exists(icon_path):
        # 设置窗口图标
        root.iconbitmap(default=icon_path)
        # 确保任务栏图标与窗口图标一致
        root.wm_iconbitmap(icon_path)
    else:
        print(f"图标文件不存在: {icon_path}")
    
    app = mkTodo(root)
    
    # 居中显示窗口
    window_width = 450
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    root.deiconify()  # 显示窗口
    root.mainloop()
