
# clean slate
rm -rf ./conda
conda-build purge-all

conda config --set anaconda_upload yes

platform=`uname`
chip=`uname -m`
if [ $platform == "Darwin" ] ; then
    if [ $chip == "arm64" ] ; then
        plat='osx-arm64'
    else
        plat='osx-64'
    fi
else
    plat='linux-64'
fi

# current dir (assume that is the package name)
name=${PWD##*/}

# conda skeleton with meta info
conda skeleton pypi --output-dir conda $name

# for for each version of python
for pythonversion in 3.10 3.11 3.12 ; do
    conda-build --python $pythonversion $@ conda/$name
done

# upload osx versions and convert to other architectures (assuming python only)
for path in `find $CONDA_PREFIX/conda-bld/$plat/ -name "$name-[0-9]*.bz2"`; do
    anaconda upload $path
    conda convert --platform all $path -o outputdir/
done

# upload versios for other architectures
for path in `find outputdir -name '*.bz2'`; do 
    anaconda upload --user munch-group $path
done

