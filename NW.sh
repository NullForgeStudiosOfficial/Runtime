#!/bin/bash

Action="$1"
Arg1="$2"
Arg2="$3"
Arg3="$4"

case "$Action" in

    SafetyCheck)
        if pgrep -x "NullWire" > /dev/null; then
            echo "yes"
        else
            echo "no"
        fi
    ;;


    #-------------------------------------- Sinks
    CreateSink)
        if pactl list short sinks | awk '{print $2}' | grep -Fxq "$Arg1"; then
            exit 0
        fi

        pactl load-module module-null-sink \
            sink_name="$Arg1" \
            sink_properties=device.description="$Arg1"
        exit 0
    ;;

    CreateMic)
        pactl list short modules | grep -q "source_name=$Arg1"

        if [[ $? -eq 0 ]]; then
            exit 0
        fi

        pactl load-module module-remap-source \
            master="$Arg2" \
            source_name="$Arg1" \
            source_properties=device.description="$Arg1"

        exit 0
    ;;

    DeleteSink)
        ModuleId=$(pactl list short modules | grep "sink_name=$Arg1" | awk '{print $1}')

        if [[ -n "$ModuleId" ]]; then
            echo "Deleting sink: $Arg1"
            pactl unload-module "$ModuleId"
        fi

        exit 0
    ;;

    DeleteMic)
        MicName="$Arg1"

        pactl list short modules | \
        grep "source_name=$MicName" | \
        awk '{print $1}' | while read -r ModuleId; do

            echo "Deleting mic: $MicName ($ModuleId)"
            pactl unload-module "$ModuleId"

        done

        exit 0
    ;;

    ClearSinks)
        pactl unload-module module-null-sink 2>/dev/null || \
        pactl list short modules | grep module-null-sink | awk '{print $1}' | while read -r Id; do
            pactl unload-module "$Id"
        done

        exit 0
    ;;

    SetSinkVolume)
        Sink="$Arg1"
        Volume="$Arg2%"
        Muted="$Arg3"

        if [[ "$Muted" == "1" || "$Muted" == "True" || "$Muted" == "true" ]]; then
            Volume="0%"
        fi

        pactl set-sink-volume "$Sink" "$Volume"
        exit 0
    ;;

    SetUnattachedVolume)
        Source="$Arg1"
        Volume="$Arg2%"

        pactl list sink-inputs | while read -r line; do

            if [[ "$line" == *"Sink Input #"* ]]; then
                Id=$(echo "$line" | awk '{print $3}' | tr -d '#')
            fi

            if [[ "$line" == *"application.name"* && "$line" == *"$Source"* ]]; then
                pactl set-sink-input-volume "$Id" "$Volume"
            fi

        done

        exit 0
    ;;

    SetMicSinkVolume)
        Sink="$Arg1"
        Volume="$Arg2%"
        Muted="$Arg3"

        if [[ "$Muted" == "1" || "$Muted" == "True" || "$Muted" == "true" ]]; then
            Volume="0%"
        fi

        pactl set-source-volume "$Sink" "$Volume"
        exit 0
    ;;

    #------------------------------------------ Aux 
    ConnectSinkToAux)
        Sink="$Arg1"
        Device="$Arg2"
        Mono="$Arg3"

        OutputPorts=$(pw-link -i | grep "$Device")

        if echo "$OutputPorts" | grep -q "playback_MONO"; then

            pw-link "$Sink:monitor_FL" "$Device:playback_MONO" 2>/dev/null || true
            pw-link "$Sink:monitor_FR" "$Device:playback_MONO" 2>/dev/null || true

        elif [[ "$Mono" == "1" || "$Mono" == "True" || "$Mono" == "true" ]]; then
            
            pw-link "$Sink:monitor_FL" "$Device:playback_FL" 2>/dev/null || true
            pw-link "$Sink:monitor_FL" "$Device:playback_FR" 2>/dev/null || true
            pw-link "$Sink:monitor_FR" "$Device:playback_FL" 2>/dev/null || true
            pw-link "$Sink:monitor_FR" "$Device:playback_FR" 2>/dev/null || true

        else
            pw-link -d "$Sink:monitor_FL" "$Device:playback_FR" 2>/dev/null || true 
            pw-link -d "$Sink:monitor_FR" "$Device:playback_FL" 2>/dev/null || true 
            pw-link "$Sink:monitor_FL" "$Device:playback_FL" 2>/dev/null || true
            pw-link "$Sink:monitor_FR" "$Device:playback_FR" 2>/dev/null || true

        fi

        exit 0
    ;;

    RemoveSinkFromAux)
        Sink="$Arg1"
        Device="$Arg2"

        OutputPorts=$(pw-link -i | grep "$Device")

        if echo "$OutputPorts" | grep -q "playback_MONO"; then

            pw-link -d "$Sink:monitor_FL" "$Device:playback_MONO" 2>/dev/null
            pw-link -d "$Sink:monitor_FR" "$Device:playback_MONO" 2>/dev/null

        else

            pw-link -d "$Sink:monitor_FL" "$Device:playback_FL" 2>/dev/null
            pw-link -d "$Sink:monitor_FR" "$Device:playback_FR" 2>/dev/null
            pw-link -d "$Sink:monitor_FL" "$Device:playback_FR" 2>/dev/null
            pw-link -d "$Sink:monitor_FR" "$Device:playback_FL" 2>/dev/null

        fi
    ;;

    DisconnectAllSinkToAux)
        Sink="$Arg1"

        pw-link -l | grep "$Sink:monitor" | while read -r line; do
            Source=$(echo "$line" | awk '{print $1}')
            Target=$(echo "$line" | awk '{print $3}')
            pw-link -d "$Source" "$Target" 2>/dev/null
        done
        exit 0
    ;;

    SetAuxVolume)
        Device="$Arg1"
        Volume="$Arg2%"
        Muted="$Arg3"

        if [[ "$Muted" == "1" || "$Muted" == "True" || "$Muted" == "true" ]]; then
            Volume="0%"
        fi

        pactl list short sinks | while read -r Id SinkName Rest; do

            if [[ "$SinkName" == "$Device" ]]; then
                pactl set-sink-volume "$SinkName" "$Volume"
                exit 0
            fi

        done
        exit 0
    ;;

    #------------------------------------------ Mic


    SetMicVolume)
        Mic="$Arg1"
        Volume="$Arg2%"
        Muted="$Arg3"

        if [[ "$Muted" == "1" || "$Muted" == "True" || "$Muted" == "true" ]]; then
            Volume="0%"
        fi

        pactl list short sources | while read -r Id SourceName Rest; do

            if [[ "$SourceName" == "$Mic" ]]; then
                pactl set-source-volume "$SourceName" "$Volume"
                exit 0
            fi

        done
        exit 0
    ;;
    

    
    #---------------------------------------------Sources
    ConnectSourceToSink)
        InputName="$Arg1"
        TargetSink="$Arg2"
        Mono="$Arg3"
 
        echo "Attach $InputName → $TargetSink"


        pactl list sink-inputs | while read -r line; do



            if [[ "$line" == *"Sink Input #"* ]]; then
                Id=$(echo "$line" | awk '{print $3}' | tr -d '#')
            fi

            if [[ "$line" == *"application.name"* && "$line" == *"$InputName"* ]]; then


                echo "Moving input $Id → $TargetSink"
                pactl move-sink-input "$Id" "$TargetSink"

                if [[ "$Mono" == "1" || "$Mono" == "True" || "$Mono" == "true" ]]; then

                    sleep 0.1

                    pw-link "$InputName:output_FL" "$TargetSink:playback_FL" 2>/dev/null || true
                    pw-link "$InputName:output_FL" "$TargetSink:playback_FR" 2>/dev/null || true
                    pw-link "$InputName:output_FR" "$TargetSink:playback_FL" 2>/dev/null || true
                    pw-link "$InputName:output_FR" "$TargetSink:playback_FR" 2>/dev/null || true

                
                else
                    pw-link -d "$InputName:output_FL" "$TargetSink:playback_FR" 2>/dev/null || true 
                    pw-link -d "$InputName:output_FR" "$TargetSink:playback_FL" 2>/dev/null || true 
                    pw-link "$InputName:output_FL" "$TargetSink:playback_FL" 2>/dev/null || true
                    pw-link "$InputName:output_FR" "$TargetSink:playback_FR" 2>/dev/null || true
                fi
            fi

        done

        exit 0
    ;;

    RemoveSourceFromSink)
        InputName="$Arg1"

        echo "Detach $InputName → default"

        DefaultSink=$(pactl get-default-sink)

        pactl list sink-inputs | while read -r line; do

            if [[ "$line" == *"Sink Input #"* ]]; then
                Id=$(echo "$line" | awk '{print $3}' | tr -d '#')
            fi

            if [[ "$line" == *"application.name"* && "$line" == *"$InputName"* ]]; then
                echo "Moving input $Id → $DefaultSink"
                pactl move-sink-input "$Id" "$DefaultSink"
            fi

        done

        exit 0
    ;;


    SetSourceVolume)
        Source="$Arg1"
        Volume="$Arg2%"
        Muted="$Arg3"

        if [[ "$Muted" == "1" || "$Muted" == "True" || "$Muted" == "true" ]]; then
            Volume="0%"
        fi

        pactl list sink-inputs | while read -r line; do

            if [[ "$line" == *"Sink Input #"* ]]; then
                Id=$(echo "$line" | awk '{print $3}' | tr -d '#')
            fi

            if [[ "$line" == *"application.name"* && "$line" == *"$Source"* ]]; then
                pactl set-sink-input-volume "$Id" "$Volume"
            fi

        done

        exit 0
    ;;

    

    

esac