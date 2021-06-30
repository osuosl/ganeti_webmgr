# -*- mode: ruby -*-
# vi: set ft=ruby :

MOUNT_POINT = '/home/vagrant/ganeti_webmgr'

Vagrant.configure("2") do |config|
  config.vm.hostname = "gwm.example.org"
  config.vm.box       = "bento/centos-6.8"

  config.vm.provider 'virtualbox' do |v|
    v.customize ['modifyvm', :id, '--cableconnected1', 'on']
  end

  config.vm.network :private_network, ip: "33.33.33.100", adapter: 2

  config.berkshelf.berksfile_path = "chef/Berksfile"
  config.berkshelf.enabled = true
  config.omnibus.chef_version = "11.12.4"

  # Symlink our project for development purposes
  config.vm.synced_folder ".", MOUNT_POINT

  config.vm.provision :chef_solo do |chef|
    chef.environments_path = "chef/environments"
    chef.environment = "vagrant"
    chef.data_bags_path = "chef/data_bags"
    chef.encrypted_data_bag_secret_key_path = "chef/encrypted_data_bag_secret"

    chef.json = {
      :mysql => {
        :server_root_password => 'rootpass',
        :server_debian_password => 'debpass',
        :server_repl_password => 'replpass'
      }
    }
    chef.run_list = [
        "recipe[ganeti_webmgr::mysql]",
        "recipe[ganeti_webmgr::bootstrap_user]",
        "recipe[ganeti_webmgr::apache]"
    ]
  end
end
