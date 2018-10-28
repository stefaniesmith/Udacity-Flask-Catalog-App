# Python Flask Catalog Application


## Setup and Configuration

To run the catalog application, it is recommended that you first set up the Ubuntu virtual machine (VM) that comes preloaded with Python, the PostgreSQL database and other supporting software. The following sections provide information on VM setup, adding items to the catalog database and launching the application.

#### Prerequisites

To set up the VM, you will need both Vagrant and VirtualBox. If you do not have these currently installed, they can be obtained from:

- [the vagrantup.com download page](https://www.vagrantup.com/downloads.html)
- [the virtualbox.org download page](https://www.virtualbox.org/wiki/Downloads) 

#### Set up the virtual machine

Fork and clone the following Github repository:

<https://github.com/udacity/fullstack-nanodegree-vm>

From the command prompt, `cd` into the `fullstack-nanodegree-vm/vagrant` directory, and run the following to create and configure the VM:
```sh
$ vagrant up
```
Note: this command may take some time to run.

Next, establish an SSH session with the VM:
```sh
$ vagrant ssh
```

#### Add the catalog application to the virtual machine

Download or clone this repository, and add the contents to the `vagrant` directory which is shared with the VM.


#### Add categories and books to the database

The `add_books.py` script should be run before launching the catalog application. This script will add a series of categories to the database (including Action/Adventure, Mystery and Science Fiction). It will also create some sample users and books. If you would like to create any additional categories, this can be done by modifying the python script.  

From the command prompt (while still in the SSH session from above), run the following to set up and add items to the database:

```sh
$ cd /vagrant
$ python add_books.py
```

After running the script, you should see a `catalog.db` file in the `/vagrant` directory.

#### Launch and access the application

The catalog application can be launched by running the `app.py` script:

```sh
$ python app.py
```

The application can then be accessed at <http://localhost:5000> from your favorite browser.

## API Endpoints

Several endpoints are available to extract information from the database in json format.

Book categories:
<http://localhost:5000/categories/json>

Information on all books in a category:
<http://localhost:5000/category/&lt;category_id&gt;/json>

Information on a book:
<http://localhost:5000/book/&lt;book_id&gt;/json>


