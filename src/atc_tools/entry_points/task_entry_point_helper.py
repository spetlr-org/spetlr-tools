from typing import List

from atc.entry_points import TaskEntryPoint

from atc_tools.helpers import ModuleHelper


class TaskEntryPointHelper:
    @staticmethod
    def get_all_task_entry_points(
        packages: List[str],
        output_txt_file: str = None,
    ) -> dict:
        """
        Returns a dictionary of entry points for all `TaskEntryPoint` objects found
        in the specified packages.

        Args:
            packages (List[str]):
                A list of package names to search for `TaskEntryPoint` objects.
            output_txt_file (str, optional) default = None:
                The name of a text file to write the entry points to.

        Returns:
            dict:
                A dictionary of entry points, with a single key called
                'atc_tools.task_entry_points'. The value of the key is a list of all
                discovered `TaskEntryPoint` classes with the `task()` method
                implemented.
        """
        if not isinstance(packages, List):
            raise TypeError("The 'packages' argument need to be of type 'List'")

        entry_point_objs = {}

        for package in packages:
            entry_point_objs.update(
                ModuleHelper.get_classes_of_type(
                    package=package,
                    obj=TaskEntryPoint,
                    main_classes=False,
                    sub_classes=True,
                )
            )

        entry_points = {"atc_tools.task_entry_points": []}

        for module_and_cls, contents in entry_point_objs.items():
            entry_point_name = module_and_cls
            module_name = contents["module_name"]
            cls_name = contents["cls_name"]
            entry_points["atc_tools.task_entry_points"].append(
                f"{entry_point_name} = {module_name}:{cls_name}.task"
            )

        if output_txt_file:
            with open(output_txt_file, "w") as auto_ep_file:
                for entry_point in entry_points["atc_tools.task_entry_points"]:
                    print(f"Found entry point: {entry_point}")
                    auto_ep_file.write(f"{entry_point}\n")

        return entry_points
