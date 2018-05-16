# Exit if any of the commands exit non-zero
set -e

tox
#source .tox/py36/Scripts/activate
source .tox/py27/Scripts/activate

# Attempt to turn off Python print buffering.
# gitbash on Windows seems like it hangs for a while
# then dumps a bunch of output.
export PYTHONBUFFERED=1

#pip list
#python -m bet_on_sibyl.US_Sports.MLB.ModelMLB
python -m bet_on_sibyl.US_Sports.MLB.RunModelMLB
