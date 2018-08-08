#!/bin/bash

COLUMNS=$(tput cols)
ESC=$(printf "\e")
PS3COLOR1="$ESC[1;31m"
PS3COLOR1_THIN="$ESC[0;31m"
PS3COLOR2="$ESC[1;255m"
PS3COLOR2_THIN="$ESC[0;255m"
PS3RESETCLR="$ESC[0m"
PS3=""
rightprompt()
{
    printf "\n%s\n" "${PS3COLOR2}Type /WORD ${PS3COLOR2_THIN}to filter the list by WORD"
    printf "%s\n\n" "${PS3COLOR2}Enter q ${PS3COLOR2_THIN}to quit${PS3RESETCLR}";
}

# PS3="$(tput sc; rightprompt; tput rc)${PS3COLOR1}Your choice: $PS3RESETCLR"
PS3="$(tput sc; rightprompt; tput rc)${PS3COLOR1}Input: ${PS3RESETCLR}"

unset options i
unset f_name j
while IFS= read -r -d $'\0' f; do
    options[i++]="$f";
    s="${f##*/}";
    f_name[j++]="${s%.inp}";
done < <(find ${1:-.} -type f -name "${2}*.inp" -print0 | sort -z -V)

select opt in "${f_name[@]}"; do
    if [[ "$REPLY" =~ ^([qQ]) ]]; then
        echo "Qutting...";
        break;
    elif [[ "$REPLY" =~ ^"/" ]]; then
        echo "Filtering...";
        exec $0 . ${REPLY#"/"};
    fi
    case $opt in
        ""|" ")
            echo "This is not an option"
            ;;
        *)
            export INP_PATH=${options[$REPLY-1]};
            # echo "${PS3COLOR1}------- selected $opt -------${PS3RESETCLR}";
            # echo "${PS3COLOR1}-----------------------------${PS3RESETCLR}";
            echo -e "\nselected $opt ---- INP_PATH set to $INP_PATH\n";
            break
            ;;
    esac
done
