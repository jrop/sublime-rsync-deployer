import sublime, sublime_plugin, subprocess, os.path

class DeployerRsyncShowStatusCommand(sublime_plugin.TextCommand):
	def run(self, edit, status):
		self.view.insert(edit, 0, status)
		self.view.set_read_only(False)
		self.view.set_scratch(True)

class DeployerRsyncDeployCommand(sublime_plugin.TextCommand):
	def display_text(self, text):
		''' Show 'text' in a new file '''
		
		newView = self.view.window().new_file()
		newView.run_command('deployer_rsync_show_status', { 'status': text })

	def shell_cmd(self, shell):
		''' Run the given shell command using bash, and the users' environment '''
		
		directoryName = os.path.dirname(self.view.window().project_file_name()) + '/'
		cmd = subprocess.Popen('source ~/.profile && ' + shell, shell=True, executable='/bin/bash', cwd=directoryName, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = cmd.communicate()
		return (cmd.returncode, out.decode('utf-8'), err.decode('utf-8'))

	def __publishTo(self, deployTarget, clean, dryRun):
		''' Run rsync and pre-build command (if defined) '''

		print('Publishing to ' + deployTarget['name'])
		print('Clean?', clean)
		print('Dry-Run?', dryRun)

		rsync = self.view.settings().get('rsync')
		directoryName = os.path.dirname(self.view.window().project_file_name()) + '/'

		#
		# BEGIN build rsync command
		#
		cmd = [ 'rsync' ]
		if dryRun:
			cmd.append('-avn')
		else:
			cmd.append('-av')

		if clean:
			cmd.append('--delete')

		if 'source_directory' in rsync:
			cmd.append(directoryName + rsync['source_directory'])
		else:
			cmd.append(directoryName + '.build/')

		cmd.append(deployTarget['dest'])
		cmd = ' '.join(cmd)
		#
		# END build rsync command
		#

		print(cmd)

		sublime.status_message('Running rsync')
		(stat, out, err) = self.shell_cmd(cmd)
		self.display_text('STDOUT:\n' + out + '\n\nSTDERR:\n' + err)

	def run(self, edit):
		print('deployer_rsync_deploy')

		#
		# BEGIN validation
		#
		if self.view.window().project_file_name() == None:
			sublime.status_message('Could not open project file.')
			return

		s = self.view.settings()
		if not self.view.settings().has('rsync'):
			sublime.status_message('There are no rsync options defined in settings.')
			return

		rsync = self.view.settings().get('rsync')
		if not 'deploy_targets' in rsync:
			sublime.status_message('Sub-option "deploy_targets" not found in "rsync".')
			return

		deployTargets = rsync['deploy_targets']
		valid = all(map(lambda target: 'name' in target and 'dest' in target, deployTargets))
		if not valid:
			sublime.status_message('Some (or all) deploy_targets do not have all required attributes "name" and "dest".')
			return
		#
		# END validation
		#

		deployNames = list(map(lambda target: target['name'], deployTargets))
		self.view.window().show_quick_panel(deployNames, self.deploy_target_selected, sublime.MONOSPACE_FONT, 0)

	def deploy_target_selected(self, index):
		if index == -1:
			return

		deployTarget = self.view.settings().get('rsync')['deploy_targets'][index]
		def which_publish(i):
			clean = True if i == 2 or i == 3 else False
			dryRun = True if i == 1 or i == 3 else False
			def confirm(i):
				if i == 1:
					self.__publishTo(deployTarget, clean, dryRun)

			self.view.window().show_quick_panel([ 'Cancel', 'Continue' ], confirm, sublime.MONOSPACE_FONT, 0)

		self.view.window().show_quick_panel([
			'Publish to ' + deployTarget['name'],
			'Publish to ' + deployTarget['name'] + ' (dry-run)',
			'Clean Publish to ' + deployTarget['name'],
			'Clean Publish to ' + deployTarget['name'] + ' (dry-run)'
		], which_publish, sublime.MONOSPACE_FONT, 0)
