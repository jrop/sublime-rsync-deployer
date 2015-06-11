all:
	mkdir -p ./.build/deployer/
	cp deployer.py deployer.sublime-commands ./.build/deployer/

	cd ./.build/; zip -r deployer.sublime-package ./deployer/
	mv ./.build/deployer.sublime-package .
	
clean:
	rm -rf ./.build/
	rm -f deployer.sublime-package
