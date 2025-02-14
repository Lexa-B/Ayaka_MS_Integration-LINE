rm -rf .*Zone.Identifier # Remove dotfiles too
rm -rf *Zone.Identifier # Remove files in the root directory
rm -rf **/*Zone.Identifier # Remove files in the subdirectories
find -type f -name "*Zone.Identifier" -delete; rm *~ # get hidden files too
find -type f -name ".*Zone.Identifier" -delete; rm *~ # get hidden files too