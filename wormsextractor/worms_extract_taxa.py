#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Copyright (c) 2019-present SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import pathlib

from wormsextractor import worms_rest_client


class SharkSpeciesListGenerator:
    """ 
        For usage instructions check "https://github.com/sharkdata/species".
    """

    def __init__(self, data_in_path="data_in", data_out_path="data_out"):
        """ """
        self.data_in_path = data_in_path
        self.data_out_path = data_out_path
        self.clear()
        # Create client for the REST API.
        self.worms_client = worms_rest_client.WormsRestWebserviceClient()
        #
        self.define_out_headers()

    def clear(self):
        """ """
        # Indata:
        self.indata_name_list = []
        self.indata_aphia_id_list = []
        self.old_taxa_worms_dict = {}  # Key: scientific_name.
        self.old_taxa_worms_by_aphia_id_dict = {}  # Key: AphiaID.
        self.old_translate_worms_dict = {}  # Key: scientific_name.
        self.old_translate_worms_by_aphia_id_dict = {}
        # Outdata.
        self.taxa_worms_header = {}
        self.taxa_worms_dict = {}  # Key: scientific_name.
        self.taxa_worms_by_aphia_id_dict = {}  # Key: AphiaID.
        self.translate_to_worms_header = {}
        self.translate_to_worms_dict = {}  # Key: scientific_name.
        self.errors_list = []  # Errors.
        # Working area.
        self.new_aphia_id_list = []
        self.higher_taxa_dict = {}  # Key: aphia_id.

    def define_out_headers(self):
        """ """
        self.translate_to_worms_header = [
            "scientific_name_from",
            "aphia_id_from",
            "dyntaxa_from",
            "scientific_name_to",
            "aphia_id_to",
            "dyntaxa_to",
        ]

        self.rename_worms_header_items = {
            "AphiaID": "aphia_id",
            "valid_AphiaID": "valid_aphia_id",
            "scientificname": "scientific_name",
        }

        self.taxa_worms_header = [
            "scientific_name",
            "rank",
            "aphia_id",
            "parent_name",
            "parent_id",
            "authority",
            "status",
            "kingdom",
            "phylum",
            "class",
            "order",
            "family",
            "genus",
            "classification",
            #             'isBrackish',
            #             'isExtinct',
            #             'isFreshwater',
            #             'isMarine',
            #             'isTerrestrial',
            #             'unacceptreason',
            #             'valid_AphiaID',
            #             'valid_authority',
            #             'valid_name',
            #             'citation',
            #             'url',
            #             'lsid',
            #             'match_type',
            #             'modified',
        ]

    def run_all(self):
        """ """
        print("\nSpecies list generator started.")

        self.read_indata_files()

        self.prepare_list_of_taxa()

        self.check_taxa_in_worms()
        self.save_results()

        self.add_higher_taxa()
        self.save_results()

        self.add_parent_info()
        self.save_results()

        self.add_old_taxa()
        self.add_old_translate()
        self.add_classification()

        self.save_results()

        print("\nDone...")

    def read_indata_files(self):
        """ 
            Import list containing scientific names or aphia_id.
            The "indata_taxa_by_aphia_id.txt" list can be used for taxa 
            that are problematic to automatically find in WoRMS.
            Also imports old versions of "taxa" and "translate" if they are available.
            Copy them from the "data_out" folder to the "data_in" folder if you 
            just want to add a few new taxa to the lists. 
        """
        self.import_taxa_by_name()
        self.import_taxa_by_aphia_id()

        self.import_old_taxa_worms()
        self.import_old_translate_to_worms()

    def prepare_list_of_taxa(self):
        """ Prepare a list of all aphia ids to import. """
        self.new_aphia_id_list = []

        # Check AphiaID indata list.
        for aphia_id in self.indata_aphia_id_list:
            if aphia_id not in self.old_translate_worms_by_aphia_id_dict:
                if aphia_id not in self.old_taxa_worms_by_aphia_id_dict:
                    self.new_aphia_id_list.append(str(aphia_id))

        # Check scientific name indata list.
        for scientific_name in self.indata_name_list:
            if scientific_name not in self.old_translate_worms_dict:
                if scientific_name not in self.old_taxa_worms_dict:

                    print("Preparing: ", scientific_name)

                    aphia_id, error = self.worms_client.get_aphia_id_by_name(
                        scientific_name
                    )
                    if error:
                        # self.errors_list.append([scientific_name, "", error])
                        aphia_id = ""
                    if aphia_id:
                        self.new_aphia_id_list.append(str(aphia_id))
                    else:
                        # Try to check if there is one accepted taxa in a list of records.
                        record_list, error = self.worms_client.get_records_by_name(
                            scientific_name
                        )
                        if error:
                            self.errors_list.append([scientific_name, "", error])
                            aphia_id = ""
                        else:
                            # Or at least an accepted name connected to the taxa.
                            translate_dict = None
                            valid_aphia_id = ""
                            valid_scientific_name = ""
                            for record_dict in record_list:
                                status = record_dict.get("status", "")
                                if status == "accepted":
                                    aphia_id = record_dict.get("AphiaID", "")
                                    self.new_aphia_id_list.append(str(aphia_id))
                                    valid_aphia_id = ""
                                    valid_scientific_name = ""
                                    break
                                # Check for valid taxa.
                                valid_aphia_id = record_dict.get(
                                    "valid_AphiaID", valid_aphia_id
                                )
                                valid_scientific_name = record_dict.get(
                                    "valid_name", valid_scientific_name
                                )
                            # No valid, but an accepted one.
                            if valid_aphia_id and valid_scientific_name:
                                translate_dict = {}
                                translate_dict["scientific_name_from"] = scientific_name
                                translate_dict[
                                    "scientific_name_to"
                                ] = valid_scientific_name
                                translate_dict["aphia_id_from"] = ""
                                translate_dict["aphia_id_to"] = valid_aphia_id
                                #
                                self.translate_to_worms_dict[
                                    scientific_name
                                ] = translate_dict

    def check_taxa_in_worms(self):
        """ """
        # Iterate over taxa.
        for aphia_id in sorted(self.new_aphia_id_list):

            worms_rec, error = self.worms_client.get_record_by_aphiaid(aphia_id)
            if error:
                self.errors_list.append(["", aphia_id, error])
            else:
                # Replace 'None' by space.
                for key in worms_rec.keys():
                    if worms_rec[key] in ["None", None]:
                        worms_rec[key] = ""
                # Translate keys from WoRMS.
                for from_key, to_key in self.rename_worms_header_items.items():
                    worms_rec[to_key] = worms_rec.get(from_key, "")
                #
                aphia_id = worms_rec.get("AphiaID", "")
                scientific_name = worms_rec.get("scientificname", "")
                valid_aphia_id = worms_rec.get("valid_AphiaID", "")
                valid_name = worms_rec.get("valid_name", "")

                print("Processing: ", scientific_name)

                # Use valid taxa.
                if aphia_id == valid_aphia_id:
                    self.taxa_worms_dict[scientific_name] = worms_rec
                    self.taxa_worms_by_aphia_id_dict[aphia_id] = worms_rec
                else:
                    # aphia_id, error = worms_rest_client.get_aphia_id_by_name(valid_name)
                    if valid_name not in self.taxa_worms_dict:
                        (worms_rec, error,) = self.worms_client.get_record_by_aphiaid(
                            valid_aphia_id
                        )
                        if error:
                            self.errors_list.append(["", valid_aphia_id, error])
                        # Replace 'None' by space.
                        for key in worms_rec.keys():
                            if worms_rec[key] in ["None", None]:
                                worms_rec[key] = ""
                        # Translate keys from WoRMS.
                        for (
                            from_key,
                            to_key,
                        ) in self.rename_worms_header_items.items():
                            worms_rec[to_key] = worms_rec.get(from_key, "")
                        #
                        self.taxa_worms_dict[valid_name] = worms_rec
                        self.taxa_worms_by_aphia_id_dict[valid_aphia_id] = worms_rec
                    # Add invalid names to translate file.
                    if scientific_name not in self.translate_to_worms_dict:
                        translate_dict = {}
                        translate_dict["scientific_name_from"] = scientific_name
                        translate_dict["scientific_name_to"] = valid_name
                        translate_dict["aphia_id_from"] = aphia_id
                        translate_dict["aphia_id_to"] = valid_aphia_id
                        self.translate_to_worms_dict[scientific_name] = translate_dict

                # Step 5. Create classification dictionary.
                (worms_rec, error,) = self.worms_client.get_classification_by_aphiaid(
                    valid_aphia_id
                )
                if error:
                    self.errors_list.append(["", valid_aphia_id, error])
                # Replace 'None' by space.
                for key in worms_rec.keys():
                    if worms_rec[key] in ["None", None]:
                        worms_rec[key] = ""
                # Translate keys from WoRMS.
                for from_key, to_key in self.rename_worms_header_items.items():
                    worms_rec[to_key] = worms_rec.get(from_key, "")
                #
                aphia_id = None
                rank = None
                scientific_name = None
                current_node = worms_rec
                while current_node is not None:
                    parent_id = aphia_id
                    #                             parent_rank = rank
                    parent_name = scientific_name
                    aphia_id = current_node.get("AphiaID", "")
                    rank = current_node.get("rank", "")
                    scientific_name = current_node.get("scientificname", "")
                    if aphia_id and rank and scientific_name:
                        taxa_dict = {}
                        taxa_dict["aphia_id"] = aphia_id
                        taxa_dict["rank"] = rank
                        taxa_dict["scientific_name"] = scientific_name
                        taxa_dict["parent_id"] = parent_id
                        taxa_dict["parent_name"] = parent_name
                        # Replace 'None' by space.
                        for key in taxa_dict.keys():
                            if taxa_dict[key] in ["None", None]:
                                taxa_dict[key] = ""
                        if aphia_id not in self.higher_taxa_dict:
                            self.higher_taxa_dict[aphia_id] = taxa_dict
                        current_node = current_node.get("child", None)
                    else:
                        current_node = None

    def add_higher_taxa(self):
        """ Add higher taxa to WoRMS dictionary. """
        for aphia_id, worms_dict in self.higher_taxa_dict.items():
            scientific_name = worms_dict.get("scientific_name", "")
            if scientific_name not in self.taxa_worms_dict:

                print("- Processing higher taxa: ", scientific_name)

                worms_rec, error = self.worms_client.get_record_by_aphiaid(aphia_id)
                if error:
                    self.errors_list.append(["", aphia_id, error])
                # Replace 'None' by space.
                for key in worms_rec.keys():
                    if worms_rec[key] in ["None", None]:
                        worms_rec[key] = ""
                # Translate keys from WoRMS.
                for from_key, to_key in self.rename_worms_header_items.items():
                    worms_rec[to_key] = worms_rec.get(from_key, "")

                self.taxa_worms_dict[scientific_name] = worms_rec
                self.taxa_worms_by_aphia_id_dict[aphia_id] = worms_rec

    def add_parent_info(self):
        """ Add parent info to built classification hierarchies. """
        for taxa_dict in self.taxa_worms_dict.values():
            aphia_id = taxa_dict.get("AphiaID", "")
            higher_taxa_dict = self.higher_taxa_dict.get(aphia_id, None)
            if higher_taxa_dict:
                taxa_dict["parent_id"] = higher_taxa_dict.get("parent_id", "")
                taxa_dict["parent_name"] = higher_taxa_dict.get("parent_name", "")

    def add_old_taxa(self):
        """ Add old taxa. """
        for scientific_name in self.old_taxa_worms_dict.keys():
            if scientific_name not in self.taxa_worms_dict:
                self.taxa_worms_dict[scientific_name] = self.old_taxa_worms_dict[
                    scientific_name
                ]

    def add_old_translate(self):
        """ Add old translate. """
        for scientific_name in self.old_translate_worms_dict.keys():
            if scientific_name not in self.translate_to_worms_dict:
                self.translate_to_worms_dict[
                    scientific_name
                ] = self.old_translate_worms_dict[scientific_name]

    def add_classification(self):
        """ Add classification. """
        for scientific_name in list(self.taxa_worms_dict.keys()):
            classification_list = []
            taxon_dict = self.taxa_worms_dict[scientific_name]
            name = taxon_dict['scientific_name']
            level_counter = 0  # To avoid recursive enless loops.
            while len(name) > 0:
                if level_counter > 20:
                    print("Warning: Too many levels in classification for: " + scientific_name)
                    break
                level_counter += 1
                classification_list.append(
                    "["
                    + taxon_dict.get("rank", "")
                    + "] "
                    + taxon_dict.get("scientific_name", "")
                )
                # # Parents.
                # parent_name = taxon_dict.get("parent_name", "")
                # taxon_dict = self.taxa_worms_dict.get(parent_name, None)
                # Parents.
                parent_id = taxon_dict.get("parent_id", "")
                taxon_dict = self.taxa_worms_by_aphia_id_dict.get(parent_id, None)
                if taxon_dict:
                    name = taxon_dict.get('scientific_name', '')
                else:
                    name = ''
            #
            self.taxa_worms_dict[scientific_name]["classification"] = " - ".join(
                classification_list[::-1]
            )

    def save_results(self):
        """ Save the results """
        self.save_errors()
        self.save_taxa_worms()
        self.save_translate_to_worms()

    def import_taxa_by_name(self):
        """ """
        indata_species = pathlib.Path(self.data_in_path, "indata_taxa_by_name.txt")
        if indata_species.exists():
            print("Importing file: ", indata_species)
            with indata_species.open(
                "r", encoding="cp1252", errors="ignore"
            ) as indata_file:
                header = None
                for row in indata_file:
                    row = [item.strip() for item in row.strip().split("\t")]
                    if row:
                        if header is None:
                            header = row
                        else:
                            row_dict = dict(zip(header, row))
                            scientific_name = row_dict.get("scientific_name", "")
                            # if (len(scientific_name) > 4) and (" " in scientific_name):
                            #     self.indata_name_list.append(scientific_name)
                            # else:
                            #     print("- Species not valid: ", scientific_name)
                            if len(scientific_name) >= 2:
                                self.indata_name_list.append(scientific_name)
            print("")

    def import_taxa_by_aphia_id(self):
        """ """
        indata_aphia_id = pathlib.Path(self.data_in_path, "indata_taxa_by_aphia_id.txt")
        if indata_aphia_id.exists():
            print("Importing file: ", indata_aphia_id)
            with indata_aphia_id.open(
                "r", encoding="cp1252", errors="ignore"
            ) as indata_file:
                header = None
                for row in indata_file:
                    row = [item.strip() for item in row.strip().split("\t")]
                    if row:
                        if header is None:
                            header = row
                        else:
                            row_dict = dict(zip(header, row))
                            aphia_id = row_dict.get("aphia_id", "")
                            if aphia_id:
                                self.indata_aphia_id_list.append(aphia_id)
            print("")

    def import_old_taxa_worms(self):
        """ """
        indata_worms = pathlib.Path(self.data_in_path, "taxa_worms.txt")
        if indata_worms.exists():
            print("Importing file: ", indata_worms)
            with indata_worms.open(
                "r", encoding="cp1252", errors="ignore"
            ) as indata_file:
                header = None
                for row in indata_file:
                    row = [item.strip() for item in row.strip().split("\t")]
                    if header is None:
                        header = row
                    else:
                        row_dict = dict(zip(header, row))
                        scientific_name = row_dict.get("scientific_name", "")
                        aphia_id = row_dict.get("aphia_id", "")
                        if scientific_name:
                            self.old_taxa_worms_dict[scientific_name] = row_dict
                            self.old_taxa_worms_by_aphia_id_dict[aphia_id] = row_dict
            print("")

    def import_old_translate_to_worms(self):
        """ """
        indata_translate = pathlib.Path(self.data_in_path, "translate_to_worms.txt")
        if indata_translate.exists():
            print("Importing file: ", indata_translate)
            with indata_translate.open(
                "r", encoding="cp1252", errors="ignore"
            ) as indata_file:
                header = None
                for row in indata_file:
                    row = [item.strip() for item in row.strip().split("\t")]
                    if header is None:
                        header = row
                    else:
                        row_dict = dict(zip(header, row))
                        scientific_name = row_dict.get("scientific_name_from", "")
                        aphia_id = row_dict.get("aphia_id", "")
                        if scientific_name:
                            self.old_translate_worms_dict[scientific_name] = row_dict
                            self.old_translate_worms_by_aphia_id_dict[
                                aphia_id
                            ] = row_dict
            print("")

    def save_taxa_worms(self):
        """ """
        taxa_worms_file = pathlib.Path(self.data_out_path, "taxa_worms.txt")
        with taxa_worms_file.open(
            "w", encoding="cp1252", errors="ignore"
        ) as outdata_file:
            outdata_file.write("\t".join(self.taxa_worms_header) + "\n")
            for _taxa, taxa_rec in self.taxa_worms_dict.items():
                row = []
                for header_item in self.taxa_worms_header:
                    row.append(str(taxa_rec.get(header_item, "")))
                try:
                    outdata_file.write("\t".join(row) + "\n")
                except Exception as e:
                    try:
                        print(
                            "Exception when writing to taxa_worms.txt: ",
                            row[0],
                            "   ",
                            e,
                        )
                    except:
                        pass

    def save_translate_to_worms(self):
        """ """
        taxa_worms_file = pathlib.Path(self.data_out_path, "translate_to_worms.txt")
        with taxa_worms_file.open(
            "w", encoding="cp1252", errors="ignore"
        ) as outdata_file:
            outdata_file.write("\t".join(self.translate_to_worms_header) + "\n")
            for taxa_rec in self.translate_to_worms_dict.values():
                row = []
                for header_item in self.translate_to_worms_header:
                    row.append(str(taxa_rec.get(header_item, "")))
                try:
                    outdata_file.write("\t".join(row) + "\n")
                except Exception as e:
                    try:
                        print(
                            "Exception when writing to taxa_worms.txt: ",
                            row[0],
                            "   ",
                            e,
                        )
                    except:
                        pass

    def save_errors(self):
        """ """
        header = ["scientific_name", "aphia_id", "error"]
        errors_file = pathlib.Path(self.data_out_path, "errors.txt")
        with errors_file.open("w", encoding="cp1252", errors="ignore") as outdata_file:
            outdata_file.write("\t".join(header) + "\n")
            for row in self.errors_list:
                try:
                    outdata_file.write("\t".join(row) + "\n")
                except Exception as e:
                    try:
                        print(
                            "Exception when writing to taxa_worms.txt: ",
                            row[0],
                            "   ",
                            e,
                        )
                    except:
                        pass

