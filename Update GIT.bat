echo off
cls
cd robopaint
git fetch upstream
git checkout master
git merge upstream/master
git push
PAUSE