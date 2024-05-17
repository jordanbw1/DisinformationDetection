import os.path

def check_filename_for_traversal(filename):
    # Normalize the path to remove any redundant separators or up-level references
    normalized_path = os.path.normpath(filename)
    
    # Split the normalized path into its components
    path_parts = normalized_path.split(os.sep)
    
    # Check if any component of the path is ".."
    if ".." in path_parts:
        return False
    
    # Check if the path is absolute
    if os.path.isabs(filename):
        return False
    
    # Check for paths that start with "~"
    if filename.startswith("~"):
        return False
    
    return True