import sublime, sublime_plugin, subprocess, os.path
from functools import partial

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

	def shell_cmd(self, parameters):
		''' Run the given shell command using bash, and the users' environment '''
		directoryName = os.path.dirname(self.view.window().project_file_name()) + '/'
		cmd = subprocess.Popen(parameters, shell=True, executable='/bin/bash', cwd=directoryName, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = cmd.communicate()
		return (cmd.returncode, out.decode('utf-8'), err.decode('utf-8'))

	def run(self, edit):
		if self.view.window().project_file_name() is None:
			sublime.status_message('You cannot run this command in non-project contexts')
			return

		s = self.view.settings()
		if not s.has('rsync'):
			sublime.status_message('No option "rsync" found')
			return
		rsync = s.get('rsync')

		if not 'destinations' in rsync:
			sublime.status_message('No option "rsync.destinations" found')
			return
		destinations = rsync['destinations']

		if not isinstance(destinations, list):
			sublime.status_message('The option "rsync.destinations" is not a list')
			return

		valid = all(map(lambda x: isinstance(x, dict) and 'name' in x and 'destination' in x, destinations))
		if not valid:
			sublime.status_message('At least one entry in "rsync.destinations" does not have a "name" or "destination" property.')
			return

		#
		# Show destination selector:
		#
		self.view.window().show_quick_panel(
			list(map(lambda x: x['name'], destinations)),
			self.deploy_target_selected,
			sublime.MONOSPACE_FONT,
			0)

	def deploy_target_selected(self, index):
		if index == -1:
			return

		dest = self.view.settings().get('rsync')['destinations'][index]			
		self.view.window().show_quick_panel([ 'Deploy (--dry-run)', 'Deploy (normal)', 'Deploy (--dry-run --delete)', 'Deploy (--delete)' ], partial(self.type_selected, dest), sublime.MONOSPACE_FONT, 0)
	
	def type_selected(self, dest, index):
		if index == -1:
			return

		cmd = []
		if index == 0:
			cmd = [ 'rsync', '-avn' ] # --dry-run
		elif index == 1:
			cmd = [ 'rsync', '-av' ] # normal
		elif index == 2:
			cmd = [ 'rsync', '-avn', '--delete' ] # --dry-run --delete
		elif index == 3:
			cmd = [ 'rsync', '-av', '--delete' ] # --delete

		self.view.window().show_quick_panel([ 'Commit' ], partial(self.commit_selected, dest, cmd), sublime.MONOSPACE_FONT, 0)

	def commit_selected(self, dest, cmd, index):
		if index == -1:
			return

		rsync = self.view.settings().get('rsync')
		if 'exclude' in rsync:
			x = rsync['exclude']
			if isinstance(x, list):
				for exclude in x:
					cmd.extend([ '--exclude', '"' + exclude + '"' ])

		cmd.extend([ './', dest['destination'] ])
		sublime.status_message('doing it...')
		print(cmd)
		(code, out, err) = self.shell_cmd(' '.join(cmd))

		self.display_text('R-SYNC COMMAND:\n' + ' '.join(cmd) + '\n\nSTDOUT:\n' + out + '\nSTDERR:\n' + err)
