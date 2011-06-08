Runtime dynamic models with Django
==================================

This is an example project to demonstrate a number of techniques that allow
dynamic models to work. 
This was written to accompany a talk at 2011 Djangocon.eu, the text of the
talk will be provided in the documentation folder of this project and a link
to the video will be provided here when it is available.

The project is a simple survey maker, where admin users can define surveys.
The responses can then be stored in a customised table for that survey, 
made possible with a dynamic model for each survey. Tables are migrated
when relevant changes are made, using a shared cache to keep multiple
processes in sync.

This was written reasonably quickly, but effort has been made to keep it simple.
There will no doubt be typos and bugs, maybe even some conceptual problems.
Please provide any feedback you might have and I will be happy to improve this
implementation. The aim of this project is to demonstrate that dynamic models
are possible and can be made to work reliably.

