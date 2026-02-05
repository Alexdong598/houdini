import hou
import PySide2.QtWidgets
import PySide2.QtCore
from functools import partial
from distutils.version import StrictVersion


def run():
        # This is the main function that gets called by the shelf tool on the bottom ( run() )

        # Store current selection
        selection = hou.selectedNodes()
        # If it is more than one or none, abort
        # Corrected: Replaced &gt; with >
        if len(selection) > 1 or len(selection) == 0:
                hou.ui.displayMessage('Please select a single Houdini Digital Asset node to save and update version on.')
                return

        # If it is not a Houdini Digital Asset, abort
        if not selection[0].type().definition():
                hou.ui.displayMessage('Please select a single Houdini Digital Asset node to save and update version on.')
                return

        # Store as hda_node
        hda_node = selection[0]

        # The definition has a ton of useful stuff
        definition = hda_node.type().definition()
        # Where the hda is saved to
        libraryFilePath = definition.libraryFilePath()

        # Store full name
        current_full_name = hda_node.type().name()

        # Last index of the name components is the current version
        current_version_string = hda_node.type().nameComponents()[-1]
        # Split versions apart and store major and minor version in a separate variable
        current_major = current_version_string.split('.')[0]
        current_minor = current_version_string.split('.')[1]
        # Set the 3 digit revision number to 0 if the HDA is only using the single float versioning (1.0 and not 1.0.005)
        # Corrected: Replaced &lt; with <
        current_revision = 0 if len(current_version_string.split('.')) < 3 else current_version_string.split('.')[2]

        # This is how you can get to all the definitions of the Houdini Digital Asset
        all_definitions = hou.hda.definitionsInFile(libraryFilePath)
        # This sets the node to the latest version of those stored
        # hda_node.changeNodeType(all_definitions[-1].nodeTypeName())

        # We have everything we need, now let's create a custom window

        # Instantiate the VersionWindow class - at this point, I would jump over to that code - keep in mind, we will
        # return a window object and afterwards we will set it's initial state, using everything we just learned about
        # this HDA.
        version_window = VersionWindow()
        # Set window title
        version_window.setWindowTitle('Versioning for: {hda_name}'.format(hda_name=current_full_name))
        # Set current version label with current version
        version_window.current_version_label.setText(current_version_string)
        # Set current path label
        version_window.current_path_label.setText(libraryFilePath)
        # Set value of the integer editor and set the editor to not go down from there
        version_window.major_version.setValue(int(current_major))
        version_window.major_version.setMinimum(int(current_major))
        # Set value of the integer editor and set the editor to not go down from there
        version_window.minor_version.setValue(int(current_minor))
        version_window.minor_version.setMinimum(int(current_minor))
        # Set value of the integer editor and set the editor to not go down from there
        version_window.revision_version.setValue(int(current_revision))
        version_window.revision_version.setMinimum(int(current_revision))
        # Connect the button signal to the set new version command and pass the hda node and the version window as arguments
        version_window.set_version.clicked.connect(partial(set_new_version_button_command, hda_node, version_window))
        # Show the window
        version_window.show()


def set_new_version_button_command(node, version_window):
        """
        Handles the logic when the 'Create New Version' button is clicked.

        :param node: hou.Node - The selected HDA node.
        :param version_window: VersionWindow - The UI window instance.
        :return: None
        """
        library_filepath = node.type().definition().libraryFilePath()
        # Get the base name (namespace::name without version)
        name_base = '::'.join(node.type().name().split('::')[:-1])
        # Construct the new version string from the UI spin boxes
        new_version = '{major}.{minor}.{revision}'.format(
            major=version_window.major_version.value(),
            minor=version_window.minor_version.value(),
            revision=version_window.revision_version.textFromValue(version_window.revision_version.value()) # Use padded text
        )
        # Construct the full new name (namespace::name::version)
        new_name = '{name_base}::{new_version}'.format(name_base=name_base, new_version=new_version)

        # Compare the current version to the new version using StrictVersion for proper comparison
        # Corrected: Replaced &gt; with >
        if not StrictVersion(new_version) > StrictVersion(node.type().nameComponents()[-1]):
                hou.ui.displayMessage('The new version number must be higher than the current version ({current}). Please increase the version.'.format(current=node.type().nameComponents()[-1]),
                                      title='Version Error')
                return

        # Create a pop up to give the user a chance to confirm or cancel
        answer = hou.ui.displayMessage(
            'Create a new version for {node_name}?\nNew Version: {new_version}'.format(
                node_name=node.type().name(),
                new_version=new_name # Show the full new name including namespace
            ),
            title='Confirm New Version',
            buttons=['OK', 'Cancel']
        )

        # If answer 'OK' (index 0), create new version and set the node to use it
        if answer == 0:
                try:
                    # Save the current definition as a new version in the same HDA file
                    node.type().definition().copyToHDAFile(library_filepath, new_name)
                    # Refresh the definitions from the file
                    all_definitions = hou.hda.definitionsInFile(library_filepath)
                    # Find the newly created definition (should be the last one)
                    new_definition = None
                    for definition in reversed(all_definitions):
                        if definition.nodeTypeName() == new_name:
                            new_definition = definition
                            break

                    if new_definition:
                        # Change the selected node instance to use the new definition
                        node.changeNodeType(new_definition.nodeTypeName())
                        hou.ui.displayMessage('Successfully created and updated to version: {new_name}'.format(new_name=new_name), title='Success')
                    else:
                         hou.ui.displayMessage('Error: Could not find the new definition after saving.', title='Error')

                    # Close version window
                    version_window.close()
                except hou.OperationFailed as e:
                    hou.ui.displayMessage('Error creating new HDA version:\n{error}'.format(error=str(e)), title='Error')
        else:
            # User cancelled
            pass # Optionally add a message here if needed


# PySide2 UI Window Class
class VersionWindow(PySide2.QtWidgets.QMainWindow):
        """
        Custom PySide2 Window for managing HDA versioning.
        """
        def __init__(self, parent=hou.ui.mainQtWindow()):
                # Initialize the QMainWindow, setting the main Houdini window as the parent
                super(VersionWindow, self).__init__(parent)

                # --- Window Setup ---
                self.setWindowTitle('HDA Versioning Tool') # Generic title, set specifically later
                self.setMinimumWidth(450) # Set a minimum width for better layout

                # --- Main Widget and Layout ---
                main_widget = PySide2.QtWidgets.QWidget(self)
                self.setCentralWidget(main_widget)

                # Use a QVBoxLayout for the overall structure (form + button)
                global_layout = PySide2.QtWidgets.QVBoxLayout(main_widget)
                # Use a QFormLayout for labeled controls
                form_layout = PySide2.QtWidgets.QFormLayout()

                # --- UI Controls ---
                # Label to display the current version (set later)
                self.current_version_label = PySide2.QtWidgets.QLabel("?.?.?")
                self.current_version_label.setStyleSheet("font-weight: bold;") # Make it stand out

                # Label to display the HDA library path (set later)
                self.current_path_label = PySide2.QtWidgets.QLabel("...")
                self.current_path_label.setWordWrap(True) # Allow path to wrap if long

                # Separator Line
                line = PySide2.QtWidgets.QFrame()
                line.setFrameShape(PySide2.QtWidgets.QFrame.HLine) # Use Shape instead of Style
                line.setFrameShadow(PySide2.QtWidgets.QFrame.Sunken)

                # SpinBox for Major version
                self.major_version = PySide2.QtWidgets.QSpinBox()
                self.major_version.setRange(0, 999) # Set a reasonable range

                # SpinBox for Minor version
                self.minor_version = PySide2.QtWidgets.QSpinBox()
                self.minor_version.setRange(0, 999) # Set a reasonable range

                # Custom PaddedSpinBox for Revision version (e.g., 001)
                self.revision_version = PaddedSpinBox()
                self.revision_version.setRange(0, 999) # Set a reasonable range

                # Button to trigger the version creation
                self.set_version = PySide2.QtWidgets.QPushButton('Create New Version')
                self.set_version.setStyleSheet("padding: 5px;") # Add some padding

                # --- Layout Population ---
                form_layout.addRow('Current Version:', self.current_version_label)
                form_layout.addRow('Library Path:', self.current_path_label)
                # Add the separator directly to the global layout for better spacing
                global_layout.addLayout(form_layout) # Add the form layout first
                global_layout.addWidget(line) # Add the line after the form

                # Add version controls in their own layout for alignment if needed, or directly
                # Using another form layout for the version numbers keeps alignment consistent
                version_layout = PySide2.QtWidgets.QFormLayout()
                version_layout.addRow('New Major Version:', self.major_version)
                version_layout.addRow('New Minor Version:', self.minor_version)
                version_layout.addRow('New Revision:', self.revision_version)
                global_layout.addLayout(version_layout) # Add version layout

                # Add the button at the bottom
                global_layout.addWidget(self.set_version)
                global_layout.addStretch() # Add stretch to push elements up


# Custom QSpinBox subclass for zero-padded revision numbers
class PaddedSpinBox(PySide2.QtWidgets.QSpinBox):
        """
        A QSpinBox that displays its value padded with leading zeros (e.g., 001, 010, 100).
        Assumes a padding width of 3.
        """
        def __init__(self, parent=None):
                super(PaddedSpinBox, self).__init__(parent)
                self.padding_width = 3 # Define padding width

        # Override valueFromText to handle potentially padded input (though QSpinBox usually handles this)
        def valueFromText(self, text):
                # Standard QSpinBox implementation is usually sufficient,
                # but we can ensure it handles integers correctly.
                try:
                    return int(text)
                except ValueError:
                    return 0 # Return 0 or self.value() if conversion fails

        # Override textFromValue to format the display text with padding
        def textFromValue(self, value):
                # Format the integer value as a string, padded with leading zeros
                return "{:0{width}d}".format(value, width=self.padding_width)

# --- Execution ---
# Check if running in Houdini before executing run()
# This prevents errors if the script is imported elsewhere.
if __name__.startswith('hou'): # A common check, though 'hou' might not be in __name__ directly
    try:
        run()
    except Exception as e:
        # Display any unexpected errors in a message box
        import traceback
        hou.ui.displayMessage("An unexpected error occurred:\n{}\n\n{}".format(str(e), traceback.format_exc()), title="Script Error")

