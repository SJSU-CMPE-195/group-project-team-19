#include "../include/interlocks.hpp"
#include <iostream>
SafetyInterlock::SafetyInterlock() {

}
void SafetyInterlock::setInterlock(Interlock interlock, Severity severity, const std::string& description ) {

    //Types of Error

    switch (severity) {

        case Severity::WARNING:
            std::cout<<"[WARNING] " << description << std::endl;
            break;

        case Severity::ERROR:
            std::cout << "[ERROR] " << description << std::endl;
            break;
        
        case Severity::CRITICAL:
            std::cout << "!!! CRITICAL SYSTEM HALT !!!" << std::endl;
            std::cout << "Reason: " << description << std::endl;

            break;
        
        default:
            std::cout << "[UNKNOWN STATUS] " << description << std::endl;
            break;

    }
}