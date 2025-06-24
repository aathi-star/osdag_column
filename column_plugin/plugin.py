"""
Column Plugin for Osdag
Main plugin class for adding Column design functionality to Osdag
"""

import os
import sys
import importlib
import traceback
from importlib.resources import files
from PyQt5.QtWidgets import QRadioButton, QWidget, QGridLayout, QButtonGroup

class ColumnPlugin:
    # Plugin metadata
    name = "Column Plugin"
    version = "0.1"
    description = "Adds Axially Loaded Column Design module to Osdag"
    author = "Osdag Team"
    
    def __init__(self):
        """
        Initialize the plugin
        """
        self.main_win = None  # Will be set by Osdag plugin manager
        
    def get_image_path(self, image_name):
        """Get path to an image resource"""
        # Try to use the image from the main osdag resources if available
        try:
            # This is the correct path format that Osdag uses for resources
            return str(files("osdag.data.ResourceFiles.images").joinpath("CompressionMembers_ColumnsInFrames.png"))
        except Exception as e:
            print(f"Error loading image from Osdag resources: {e}")
            # Fallback to plugin resources
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(plugin_dir, "column", "resources", image_name)
    
    def show_column_module(self, *args):
        """
        Launch the column design module
        This method will be added to the main window when the plugin is activated
        """
        import osdag.gui.ui_template
        from osdag.gui.ui_template import Ui_ModuleWindow
        from osdag.modules.compression_member.Column import ColumnDesign
        
        # Hide the main window
        if hasattr(self, "main_win") and self.main_win:
            self.main_win.hide()
            # Launch the column module
            ui2 = Ui_ModuleWindow(ColumnDesign, ' ')
            ui2.show()
            # Show the main window again when the module is closed
            ui2.closed.connect(self.main_win.show)
        else:
            print("Cannot launch column module: main_win not set")
            
    def find_main_window(self):
        """
        Find the real OsdagMainWindow instance via QApplication
        """
        from PyQt5.QtWidgets import QApplication
        
        # Find all top level widgets
        for widget in QApplication.topLevelWidgets():
            # Check if this is likely the OsdagMainWindow
            if hasattr(widget, 'Modules'):
                return widget
                
            # Check if it has a ui attribute that might be the main window
            if hasattr(widget, 'ui'):
                ui = widget.ui
                # Check if the ui has Modules dictionary
                if hasattr(ui, 'Modules'):
                    return ui
                
                # Check if it has myStackedWidget (a sign of OsdagMainWindow)
                if hasattr(ui, 'myStackedWidget'):
                    # This might be the main window's UI
                    if hasattr(widget, 'Modules'):
                        return widget
        
        # If we get here, we couldn't find the main window directly
        # Try harder by looking for objects with the right class name
        for widget in QApplication.topLevelWidgets():
            if widget.__class__.__name__ == 'OsdagMainWindow':
                return widget
                
        # If we still can't find it, return None
        return None
    
    def _find_modules_dict(self, window_obj):
        """
        Find the Modules dictionary in the window hierarchy
        
        Args:
            window_obj: The window object to search in
            
        Returns:
            tuple: (object with Modules, Modules dict) or (None, None) if not found
        """
        # First try the window object itself
        if hasattr(window_obj, 'Modules'):
            return window_obj, window_obj.Modules
            
        # Try ui attribute if it exists
        if hasattr(window_obj, 'ui'):
            ui = window_obj.ui
            if hasattr(ui, 'Modules'):
                return ui, ui.Modules
                
        # If we get here, we couldn't find Modules in the expected places
        # Try harder by recursively searching the widget hierarchy
        def search_for_modules(widget, visited=None):
            if visited is None:
                visited = set()
                
            # Skip if already visited (avoid infinite recursion)
            if id(widget) in visited:
                return None, None
                
            visited.add(id(widget))
            
            # Check this widget
            if hasattr(widget, 'Modules'):
                return widget, widget.Modules
                
            # Check its children
            for child in widget.children():
                result = search_for_modules(child, visited)
                if result[0] is not None:
                    return result
                    
            # Not found
            return None, None
            
        return search_for_modules(window_obj)
    
    def register(self):
        """
        Register the plugin with Osdag
        """
        print(f"Registering {self.name} version {self.version} ({self.description})")
        
        # Find the real main window (not just the plugins dialog)
        real_main_window = self.find_main_window()
        if not real_main_window:
            # Fall back to the main_win attribute set by Osdag plugin manager
            real_main_window = self.main_win
            print(f"Using main_win from plugin manager: {real_main_window}")
        else:
            print(f"Found main window: {real_main_window}")
            
        # Store reference to main window
        self.main_win = real_main_window
            
        # Find the Modules dictionary
        modules_obj, modules_dict = self._find_modules_dict(real_main_window)
        if not modules_dict:
            print("Error: Could not find Modules dictionary")
            print(f"Available attributes in main window: {dir(real_main_window)}")
            if hasattr(real_main_window, 'ui'):
                print(f"Available attributes in main window.ui: {dir(real_main_window.ui)}")
            return
            
        print(f"Found Modules dictionary in {modules_obj}")
        
        # Add the Column module to the Compression Member module
        if 'Compression Member' in modules_dict:
            compression_module = modules_dict['Compression Member']
            
            # Check if compression module is a list (as expected)
            if isinstance(compression_module, list):
                # Check if the last item is the handler function
                if callable(compression_module[-1]):
                    # Get column module image path
                    image_path = self.get_image_path("column.png")
                    
                    # Add Column entry to the compression module list
                    # Format: (display_name, image_path, radio_button_object_name)
                    column_entry = ('Axially Loaded Column', image_path, 'Column_Design')
                    
                    # Insert at the beginning of the list, preserving the handler at the end
                    modules_dict['Compression Member'].insert(0, column_entry)
                    
                    print(f"Added Column module to Compression Member module:")
                    print(f"  - Entry: {column_entry}")
                    
                    # Update the column module handler in the main window
                    # This assumes show_compression_module is already defined in main window
                    # and will check for the Column_Design radio button
                    show_column_original = real_main_window.show_compression_module
                    
                    # Import the ColumnDesign class in the main namespace for the show_column_module
                    # handler to find it when the module is selected
                    try:
                        from osdag.design_type.compression_member.Column import ColumnDesign
                        print("Successfully imported ColumnDesign class")
                    except ImportError as e:
                        print(f"Warning: Could not import ColumnDesign: {e}")
                        print("Module activation may fail if ColumnDesign class is not available")
                        
                    # Attempt to immediately update the UI
                    self._update_live_ui(real_main_window)
                    
                    # Make our plugin directory available for imports
                    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if plugin_dir not in sys.path:
                        sys.path.append(plugin_dir)
                    
                    print(f"Column Plugin activated! Column module added to Compression Member.")
                    
                else:
                    print("Error: Compression Member module doesn't have a handler function")
            else:
                print(f"Error: Compression Member module is not a list (got {type(compression_module)})")
        else:
            print("Error: Compression Member module not found in Modules dictionary")
            print(f"Available modules: {list(modules_dict.keys())}")
    
    def _update_live_ui(self, window_obj):
        """
        Update the UI to reflect changes in the modules dictionary
        """
        try:
            print("Attempting immediate UI update...")
            
            # Find the Compression Member page in the stackedWidget
            if hasattr(window_obj, 'ui') and hasattr(window_obj.ui, 'myStackedWidget'):
                stack = window_obj.ui.myStackedWidget
                
                # Look for the page with the Compression Member module
                for i in range(stack.count()):
                    page = stack.widget(i)
                    
                    # Check if this is the compression member page
                    if page is not None:
                        print(f"Found page at index {i}: {page.__class__.__name__}")
                        
                        # Check if this is likely the compression page
                        if hasattr(page, 'findChild'):
                            strut_button = page.findChild(QRadioButton, 'Strut_Design')
                            if strut_button is not None:
                                print(f"Found Compression Member page at index {i}")
                                
                                # This is the compression member page - now we need to rebuild the UI
                                # First, remove any existing Column_Design button if it exists
                                column_button = page.findChild(QRadioButton, 'Column_Design')
                                if column_button is not None:
                                    # Get its parent widget and remove it
                                    column_widget = column_button.parent()
                                    if column_widget is not None:
                                        # Remove from layout
                                        print(f"Removing existing Column button widget")
                                        if hasattr(page, 'ui') and hasattr(page.ui, 'gridLayout'):
                                            page.ui.gridLayout.removeWidget(column_widget)
                                            column_widget.deleteLater()
                                
                                # Now rebuild the module widgets using proper Osdag layout logic
                                if hasattr(page, 'ui') and hasattr(page.ui, 'gridLayout'):
                                    grid_layout = page.ui.gridLayout
                                    print(f"Found gridLayout in page")
                                    
                                    try:
                                        # Get image path using proper Osdag resource format
                                        image_path = str(files("osdag.data.ResourceFiles.images").joinpath("CompressionMembers_ColumnsInFrames.png"))
                                        
                                        # Create a widget for our column module using Osdag's widget classes
                                        from osdag.osdagMainPage import Submodule_Widget
                                        
                                        # Create module entry tuple: (name, image_path, object_name)
                                        module_tuple = ("Axially Loaded Column", image_path, "Column_Design")
                                        
                                        # Create a new widget for the column module
                                        widget = Submodule_Widget(module_tuple, page)
                                        
                                        # Find existing button group to add our radio button
                                        button_groups = page.findChildren(QButtonGroup)
                                        if button_groups:
                                            button_group = button_groups[0]
                                            button_group.addButton(widget.rdbtn)
                                        
                                        # Add to grid layout at position 0,0 (to appear first/left)
                                        grid_layout.addWidget(widget, 0, 0)
                                        
                                        # Move Strut button to position 0,1
                                        if strut_button is not None:
                                            strut_widget = strut_button.parent()
                                            if strut_widget is not None:
                                                grid_layout.removeWidget(strut_widget)
                                                grid_layout.addWidget(strut_widget, 0, 1)
                                        
                                        print("Successfully rebuilt UI with Column module")
                                        return True
                                    except Exception as e:
                                        print(f"Error creating widget: {str(e)}")
                                        traceback.print_exc()
                                else:
                                    print(f"Could not find gridLayout in page")
                                    
                                    # Try alternative approach - find any grid layout in the page
                                    grid_layouts = page.findChildren(QGridLayout)
                                    if grid_layouts:
                                        print(f"Found {len(grid_layouts)} grid layouts through findChildren")
                                        grid_layout = grid_layouts[0]
                                        # TODO: Try the same widget creation logic as above with this layout
                                    else:
                                        print("Could not find any grid layouts in the page")
            else:
                print("Could not find UI or stackedWidget for immediate update")
            
            # Method 2: Try to call refresh methods on main window
            ui_updated = False
            for method_name in ["initialize_module_buttons", "refresh_module_list", 
                               "setup_module_buttons", "update_ui"]:
                if hasattr(window_obj, method_name) and callable(getattr(window_obj, method_name)):
                    try:
                        print(f"Calling {method_name} on main window...")
                        getattr(window_obj, method_name)()
                        print(f"Successfully called {method_name}")
                        ui_updated = True
                    except Exception as e:
                        print(f"Error calling {method_name}: {e}")
            
            if ui_updated:
                print("UI update attempted through multiple methods")
                print("The Column module should now be visible in the Compression Member section")
                return True
            else:
                # If we get here, we couldn't update the UI immediately
                # The changes will still be in the Modules dictionary,
                # so they'll appear after a restart
                print("UI update failed - changes will be visible after restart")
                return False
                    
        except Exception as e:
            print(f"Error in _update_live_ui: {e}")
            traceback.print_exc()
            return False
        
        # Force update
        if hasattr(window_obj, 'update'):
            window_obj.update()
        return False
    
    def deactivate(self):
        """
        Deactivate the plugin and remove Column module from UI
        """
        print("Deactivating Column Plugin...")
        
        # Find the real main window
        real_main_window = self.find_main_window()
        if not real_main_window:
            real_main_window = self.main_win
            
        # Check if Column module is open and close it
        if hasattr(real_main_window, 'module_window') and real_main_window.module_window:
            if hasattr(real_main_window, 'module_name') and real_main_window.module_name == 'Column':
                real_main_window.module_window.close()
                
        # Find the Modules dictionary
        modules_obj, modules_dict = self._find_modules_dict(real_main_window)
        if not modules_dict:
            print("Error: Could not find Modules dictionary")
            return
            
        # Remove the Column module from the Compression Member module
        if 'Compression Member' in modules_dict:
            compression_module = modules_dict['Compression Member']
            
            # Check if compression module is a list (as expected)
            if isinstance(compression_module, list):
                # Look for the Column entry
                for i, item in enumerate(compression_module):
                    if isinstance(item, tuple) and len(item) >= 3:
                        if item[2] == 'Column_Design':
                            # Remove the entry
                            modules_dict['Compression Member'].pop(i)
                            print("Removed Column module from Compression Member module")
                            break
                            
                # Try to update the UI
                print("Attempting immediate UI update...")
                if hasattr(real_main_window, 'ui') and hasattr(real_main_window.ui, 'myStackedWidget'):
                    stack = real_main_window.ui.myStackedWidget
                    
                    # Look for the Compression Member page
                    for i in range(stack.count()):
                        page = stack.widget(i)
                        
                        # Check if this is the compression member page
                        if page is not None and hasattr(page, 'findChild'):
                            strut_button = page.findChild(QRadioButton, 'Strut_Design')
                            if strut_button is not None:
                                print(f"Found Compression Member page at index {i}")
                                
                                # Find and remove any Column_Design button
                                column_button = page.findChild(QRadioButton, 'Column_Design')
                                if column_button is not None:
                                    # Get its parent widget and remove it
                                    column_widget = column_button.parent()
                                    if column_widget is not None:
                                        # Remove from layout
                                        print(f"Removing Column button widget")
                                        if hasattr(page, 'ui') and hasattr(page.ui, 'gridLayout'):
                                            page.ui.gridLayout.removeWidget(column_widget)
                                            column_widget.deleteLater()
                                        else:
                                            print("Could not find gridLayout in page")
            else:
                print(f"Error: Compression Member module is not a list (got {type(compression_module)})")
        else:
            print("Error: Compression Member module not found in Modules dictionary")
            
        print("Column Plugin deactivated")
    
    def initialize_plugin(self):
        """
        Optional initialization code
        """
        print("Initializing Column Plugin...")
        return True
