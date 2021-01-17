"""
Messages for the Compatibility library

If you want to add languages you have to add translations for all messages.
Furthermore the order of parts to be replaced must be equal in the translation.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
(c) 2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

messages = {'check_for_updates': {
    'en': ("Your version of %s was released %s days ago. " +
            "There could be updates and security fixes."),
    'de': ("Ihre Version von %s wurde vor %s Tagen veröffentlicht. " +
           "Updates und Security-Fixes könnten bereit stehen.")
}, 'incompatible_version': {
    'en': ("Your version of the Python interpreter is not compatible" +
           " with this specific version of %s. Please check if " +
           "there are any updates that solve this."),
    'de': ("Ihre Version des Python Interpreter ist nicht kompatibel " +
           "dieser Version von %s. Bitte prüfen Sie, ob ein Update " +
           "dieses Problem löst.")
}, 'untested_interpreter': {
    'en': ("Your version of the Python interpreter is higher than " +
           "the versions this installation of %s is tested for. " +
           "Please check for updates."),
    'de': ("Ihre Version des Python-Interpreter ist neuer als alle " +
           "Versionen gegen die diese Version von %s getestet wurde." +
           " Prüfen Sie, ob es ein Update gibt.")
}, 'version_info': {
    'en': "You are using %s in version %s (%s)",
    'de': "Sie nutzen %s in Version %s (%s)"
}
}
