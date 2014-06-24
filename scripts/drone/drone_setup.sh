APPENGINE_SDK_VERSION=1.9.1
APPENGINE_SDK_ZIPFILE=google_appengine_${APPENGINE_SDK_VERSION}.zip
echo "Downloading Google App Engine SDK..."
wget --quiet http://storage.googleapis.com/tagtoo_public/google-app-engine-sdk/${APPENGINE_SDK_ZIPFILE}
echo "Extracting Google App Engine SDK..."
unzip -q ${APPENGINE_SDK_ZIPFILE} > /dev/null

echo "Installing system dependencies..."
sudo apt-get install --yes libxml2-dev libxslt1-dev > /dev/null # for lxml

echo "Installing PIP dependencies..."
pip install -r scripts/drone/requirements_test.txt > /dev/null

echo "Cloning submodules..."
git submodule init
git submodule update

echo "Start testing..."
scripts/drone/run_test.sh
test_status=$?

echo "Generating HTML Coverage Report..."
coverage html

exit $test_status
