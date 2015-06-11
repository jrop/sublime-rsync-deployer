all:
	mkdir -p ./.build/
	cp deployer.py deployer.sublime-commands ./.build/
	zip -r deployer.sublime-package ./.build/

clean:
	rm -rf ./.build/
	rm -f deployer.sublime-package
